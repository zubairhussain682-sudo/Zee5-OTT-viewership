"""Independent daily reconstruction of profile and profile-title opportunity.

The validator uses source tables directly rather than the builder's access
matrix or catalogue cube. A supplied suite must implement hard(id, name,
reference, violations, detail=None). Zero violations are required.
"""
import numpy as np
import pandas as pd


def validate_profile_opportunity(v, d, marts, windows):
    profiles = d['profiles'].reset_index(drop=True)
    ids = pd.Index(profiles.profile_id)
    parents = pd.Index(sorted(d['catalogue'].parent_title_id.unique()))
    created = pd.to_datetime(profiles.profile_created_date)
    catalogue = d['catalogue']
    cycles = d['cycles']
    audio = d['audio']
    language_col = 'language'
    if language_col not in audio:
        raise ValueError('Missing public audio-language contract')

    for label in ('BASELINE_90', 'FINAL_90'):
        start, end = windows[label]
        entitled = np.zeros(len(profiles), dtype=np.int32)
        exposure = np.zeros((len(profiles), len(parents)), dtype=np.int32)
        for day in pd.date_range(start, end):
            active = cycles[(cycles.cycle_start_date <= day.date())
                            & (cycles.cycle_end_date >= day.date())]
            if active.account_id.duplicated().any():
                raise ValueError('Ambiguous account-day entitlement in independent QA')
            state = profiles[['account_id']].merge(
                active[['account_id', 'plan_family', 'plan_language_group']],
                on='account_id', how='left', sort=False)
            exists = (created <= day).to_numpy()
            valid_family = state.plan_family.isin(['ALL_ACCESS', 'ALL_ACCESS_SPORTS', 'REGIONAL'])
            entitled += exists & valid_family.to_numpy()
            available = catalogue[
                (catalogue.catalogue_entry_date <= day)
                & (catalogue.release_date.isna() | (catalogue.release_date <= day))
                & (catalogue.catalogue_exit_date.isna() | (catalogue.catalogue_exit_date >= day))]
            title_ids = set(available.parent_title_id)
            for (family, language), group in state[valid_family].groupby(
                    ['plan_family', 'plan_language_group']):
                row_positions = group.index[exists[group.index]].to_numpy()
                eligible = title_ids
                if family == 'REGIONAL':
                    eligible = title_ids & set(
                        audio.loc[audio[language_col] == language, 'parent_title_id'])
                col_positions = parents.get_indexer(sorted(eligible))
                exposure[np.ix_(row_positions, col_positions)] += 1

        p = (marts['profile_viewership_window'].query('window_label == @label')
             .set_index('profile_id').reindex(ids))
        t = marts['profile_title_window'].query('window_label == @label')
        observable = ((end - created.clip(lower=start)).dt.days + 1).clip(lower=0).to_numpy()
        hard = lambda number, name, count, detail=None: v.hard(
            number + '_' + label, name, 'Profile opportunity contract', int(count), detail)

        for number, column in [('P01', 'entitled_days_in_window'),
                               ('P02', 'vod_entitled_days_in_window')]:
            values = p[column].to_numpy()
            hard(number, column + ' bounded by observable profile days',
                 np.sum(~np.isfinite(values) | (values < 0) | (values > observable)))

        ti, tj = (ids.get_indexer(t.profile_id), parents.get_indexer(t.parent_title_id))
        if (ti < 0).any() or (tj < 0).any():
            raise ValueError('Orphan profile/title in opportunity QA')
        values = t.available_days_in_window.to_numpy()
        hard('P03', 'Profile-title opportunity upper bound',
             np.sum(~np.isfinite(values) | (values < 0) | (values > observable[ti])))
        hard('P04', 'Every profile-title exposure equals independent historical day intersection',
             np.sum(values != exposure[ti, tj]),
             {'rows_checked': len(t),
              'oracle': 'daily public cycles, profile creation, released available assets and plan/audio eligibility'})
        hard('P05', 'Profile entitled days equal independent historical access',
             np.sum((p.entitled_days_in_window.to_numpy() != entitled)
                    | (p.vod_entitled_days_in_window.to_numpy() != entitled)))

        title_days = exposure.sum(axis=1)
        mean = title_days / np.maximum(entitled, 1)
        hard('P06', 'Profile catalogue opportunity and mean reproduce',
             np.sum((p.eligible_parent_title_days.to_numpy() != title_days)
                    | ~np.isclose(p.mean_daily_eligible_parent_titles.to_numpy(), mean,
                                  rtol=1e-12, atol=1e-12)))

        flag = ((p.vod_entitled_days_in_window >= 30)
                & (p.active_days >= 3)
                & (p.qualified_watch_minutes >= 120))
        hard('P07', 'Eligibility and component flags reproduce exactly',
             np.sum((p.is_main_analytical_eligible != flag)
                    | (p.meets_entitled_days != (p.vod_entitled_days_in_window >= 30))
                    | (p.meets_active_days != (p.active_days >= 3))
                    | (p.meets_qualified_minutes != (p.qualified_watch_minutes >= 120))))

        late = ((created >= start) & (created <= end)).to_numpy()
        hard('P08', 'Late-created profiles have no inherited pre-creation opportunity',
             np.sum(late & ((p.entitled_days_in_window.to_numpy() != entitled)
                            | (p.eligible_parent_title_days.to_numpy() != title_days))),
             {'late_profiles_checked': int(late.sum()),
              'window_start': str(start.date()),
              'window_end': str(end.date())})

        expected = p.groupby('account_id').is_main_analytical_eligible.sum()
        a = (marts['account_viewership_window'].query('window_label == @label')
             .set_index('account_id'))
        hard('P09', 'Account eligible-profile counts equal the sum of profile eligibility',
             np.sum(a.n_eligible_profiles != expected.reindex(a.index, fill_value=0)))
