-- Question:        Is a profile a distinct behavioural identity inside a commercial account?
-- Why it matters:  Subscriptions and access are held by accounts, but viewing is recorded against
--                  profiles. Treating an account as one viewer collapses several profiles' behaviour
--                  into one identity; treating a profile as the paying customer misplaces
--                  commercial state.
-- Analytical use:  Confirms every profile belongs to exactly one account and shows how often
--                  accounts hold more than one profile, which is why commercial state (account
--                  grain) and behavioural identity (profile grain) are kept separate.
-- SELECT-only. Select the intended database before running.

-- Every profile must resolve to an existing account (expected: profiles_without_account = 0).
SELECT COUNT(*) AS profiles_without_account
FROM profiles p
LEFT JOIN accounts a ON a.account_id = p.account_id
WHERE a.account_id IS NULL;

-- Profiles per account: multi-profile accounts are the reason account and profile grains differ.
SELECT profiles_in_account, COUNT(*) AS accounts
FROM (
    SELECT a.account_id, COUNT(p.profile_id) AS profiles_in_account
    FROM accounts a
    LEFT JOIN profiles p ON p.account_id = a.account_id
    GROUP BY a.account_id
) per_account
GROUP BY profiles_in_account
ORDER BY profiles_in_account;
