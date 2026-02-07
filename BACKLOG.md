# Project Backlog

## To Do
- [ ] Replace the shit popup windows
- [ ] Make income green and other's red
- [ ] Verify if link token needs to be created upon each page refresh
- [ ] Encrypt public tokens
- [ ] getting snapshot occurs too often
- [ ] Auth currently goes inactive when active (jwt token as well)
- [ ] Verify backend processes are multi-user
- [ ] Check if transactions can do time and not just date - make it so time is used
- [ ] Have a raw data table
- [ ] Currently modified syncs rewrites Manually modified categories and confidence
- [ ] Verify balances work correctly credit/loan vs others
- [ ] Optionally set the description as a pattern in a transaction_rule table

## In Progress
- [ ] Have errors go to frontend and display

## Done
- [x] Refactor - Keep exceptions/logging to services/routes/tasks
- [x] Need to be able to add accounts for institutions already added
- [x] Split up pages into their own files on dashboard
- [x] Add webhook functionality, queuing, and syncing
- [x] Confidence level changes to "Manual" if the user changes a category
- [x] Currently, rebalancing takes 1 date - it needs to take two since there are two types of calculations
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
- Something to look at - Do unselected bank accounts get synced through plaid?
- Add APR/interest
- Show income a month and year - break down by sources
- Show spending trends graph by category
- Make a budget
- Cache requirements for pytests and jest