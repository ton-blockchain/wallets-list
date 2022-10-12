# Wallets list

This repository contains the list of wallets that support TON Connect.

TON Connect [SDK](https://github.com/ton-connect/sdk) uses this list to present a choice of wallets so that dapp knows which bridge to use.

### Entry format

Each entry has the following format (subject to change):

```json
{
  name: "Tonkeeper",
  image: "https://tonkeeper.com/tonconnect-icon.png"
  tondns:  "tonkeeper.ton",
  about_url: "https://tonkeeper.com",
  universal_url: "https://app.tonkeeper.com",
  bridge_url: "https://bridge.tonkeeper.com",
}
```

### How do I add my wallet?

Submit a [pull request](https://github.com/ton-connect/wallets-list/pulls) that modifies the list.

We will review correctness of the info (obviously we want this info to be provided by the wallet’s developer) and merge it promptly.

### What is the policy?

Our goal is to represent accurate up-to-date list of all TON wallets that support TON Connect.

In the future it would be a good idea to replicate wallet's info in a TON DNS record so that this repo simply lists the wallet domain names (to filter out spam), while developers have more direct control over the wallet parameters.
