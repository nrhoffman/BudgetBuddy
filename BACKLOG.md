# Project Backlog

## To Do
- [x] Use update mode for getting additional accounts (might work?)
- [ ] Set up cloud with all services
- [ ] Replace the shit popup windows
- [ ] Verify backend processes are multi-user
- [ ] Optionally set the description as a pattern in a transaction_rule table
- [ ] Currently modified syncs rewrites Manually modified categories and confidence

## In Progress
- [ ] Switch from calculating account balances to using acc api
- [ ] Incorporate pending transactions and available balance
- [ ] Accounts should be retrieved separate from transactions. Transactions should be paginated
- [ ] Add a loading for when bank accounts are linking
- [ ] Encrypt public tokens

## Done
- [x] Fix some balance and holder account data being null
- [x] Switch to soft delete for accounts
- [x] Replace transactions/get with just transaction/sync <- test
- [x] link token generates when plaid button clicked
- [x] Getting snapshot occurs too often - make refresh manual / once a session
- [x] When adding accounts, add institution logo to Account and BankToken
- [x] Create a basic settings page
- [x] Use logo from transactions for transaction table
- [x] Get more data from transactions and accounts
- [x] Need an option to delete all user data including raw
- [x] Password rules
- [x] Verify balances work correctly credit/loan vs others
- [x] Add APR/Interest to frontend
- [x] Don't store raw data with same item_id and cursor
- [x] Add APR/interest to backend
- [x] Add whether transaction is income or expense going into database
- [x] Make income green and other's red
- [x] Make a new raw table for raw plaid data
- [x] Refactor - Keep exceptions/logging to services/routes/tasks
- [x] Need to be able to add accounts for institutions already added
- [x] Split up pages into their own files on dashboard
- [x] Add webhook functionality, queuing, and syncing
- [x] Confidence level changes to "Manual" if the user changes a category
- [x] Currently, rebalancing takes 1 date - it needs to take two since there are two types of       calculations
- [x] combined transaction add/update/remove
- [x] Reuse public tokens for each item ID
- [x] Track which institution links to which item ID
- [x] Ensure final acc balance is calculated correctly after tx category change
- [x] Fix how credit and loan balances work with transactions - charges cause number to go up
- [x] Flag categories with low confidence so user can either approve or change
- [x] The balances will need to be updates for all transaction balances after the one changed
- [x] Allow user to change transaction category and detailed category
- [x] Add a balance variable to transactions to mean the balance after the transaction takes place
- [x] Split service up and fix pytests
- [x] Fix pytests for the account update
- [x] Making accounts names editable
- [x] Changed Plaid category from legacy to modern

## Ideas
- Show income a month and year - break down by sources
- Show spending trends graph by category
- Make a budget
- Cache requirements for pytests and jest