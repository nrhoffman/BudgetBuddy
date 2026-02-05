# Project Backlog

## To Do
- [ ] Currently modified syncs rewrites Manually modified categories and confidence
- [ ] Replace the shit popup windows
- [ ] Make income green and other's red
- [ ] Verify if link token needs to be created upon each page refresh
- [ ] Encrypt public tokens
- [ ] getting snapshot occurs too often
- [ ] Auth currently goes inactive when active (jwt token as well)
- [ ] Verify backend processes are multi-user
- [ ] Check if transactions can do time and not just date - make it so time is used

## In Progress
- [ ] Need to be able to add accounts for institutions already added
- [ ] After webhook addition, set category changes
- [ ] Verify balances work correctly credit/loan vs others
- [ ] Optionally set the description as a pattern in a transaction_rule table

## Done
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
- Add APR/interest
- Show income a month and year - break down by sources
- Show spending trends graph by category
- Make a budget
- Cache requirements for pytests and jest