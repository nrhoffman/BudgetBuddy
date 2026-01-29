# Project Backlog

## To Do
- [ ] Replace the shit popup windows
- [ ] Make income green and other's red

## In Progress
- [ ] After adding account, have user go through transactions to select/confirm income and transfer_in categories
- [ ] Verify balances work correctly credit/loan vs others
- [ ] Optionally set the description as a pattern in a transaction_rule table

## Done
- [x] Fix how credit and loan balances work with transactions - charges cause number to go up
- [x] Flag categories with low confidence so user can either approve or change
- [x] The balances will need to be updates for all transaction balances after the one changed
- [x] Allow user to change transaction category and detailed category
- [x] Confidence level changes to "Manual" if the user changes a category
- [x] Add a balance variable to transactions to mean the balance after the transaction takes place
- [x] Split service up and fix pytests
- [x] Fix pytests for the account update
- [x] Making accounts names editable
- [x] Changed Plaid category from legacy to modern

## Ideas
- Show spending trends graph by category
- Make a budget
- Cache requirements for pytests and jest