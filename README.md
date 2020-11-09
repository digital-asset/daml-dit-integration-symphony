# Symphony DAML Integration

This is a DAML integration for implementing a [Symphony Messaging Bot](https://developers.symphony.com/symphony-developer/docs/overview-of-bots).

The integration is deployed configured and launched in [project:DABL](https://www.projectdabl.com). It will run as a DAML Party on your ledger that can send and receive messages as a Symphony Bot. Inbound messages, outbound messages and element actions actions and outbound messages are represented as a contract on the DAML ledger.

The integration can be setup to only send messages, only receive messages, or both send and receive messages.

### How it works
#### Inbound Messages
When the Symphony Bot receives a message, an `InboundDirectMessage` is created on the ledger with the message text as well as the sender's username and the Symphony Stream ID.

#### Outbound Messages
To send a message, create a an `OutboundMessage` contract on your ledger as the party the integration is running on, and the integration will automatically send the message to the given Symphony Stream Id and archive the contract.

**Note**: The Symphony integration will automatically wrap the `OutboundMessage`'s `message` field with the necessary `<messageML></messageML>` tags.

#### Element Actions
Symphony Elements allow a bot to send a form to a user to fill out and submit (see [Overview of Symphony Elements](https://developers.symphony.com/symphony-developer/docs/overview-of-symphony-elements)) in the Symphony documentation.

When receiving an element action as the result of an element form being submitted, an `InboundElementAction` is created with the payload information containing the response to the form as a JSON string in the contract.

To send an element form, use an `OutboundMessage` with the message payload containing the `<form>` elements as the text.

## To configure

The integration requires a [Symphony Bot User](https://developers.symphony.com/symphony-developer/docs/create-a-bot-user) and a set of RSA credentials to run as the bot user. See [here](https://developers.symphony.com/symphony-developer/docs/rsa-bot-authentication-workflow) for instructions on setting up the Symphony Bot with a private/public RSA key pair.

- **Host**: The URL of the Symphony pod host (e.g. `yourcompany.symphony.com`)
- **Port**: The port the bot should connect to on the symphony pod host
- **RSA Private Key**: The private key generated when creating the Symphony Bot User
- **Bot Username**: The username of the Symphony Bot User
- **Bot Email**: The email address associated with the Symphony Bot User
- **Token Refresh**: How often the bot should attempt to refresh the authentication token
- **Interval**: How often the integration should respond to new messages (Only necessary when receiving messages).

> This integration is under active development. Please raise any Github issues or direct your questions to the [DAML forum](https://discuss.daml.com/)
