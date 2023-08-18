# TON Connect Wallets

This repository contains the list of wallets that support TON Connect.

TON Connect [SDK](https://github.com/ton-connect/sdk) uses this list to present a choice of wallets so that dapp knows which bridge to use.

### Entry format

Each entry has the following format (subject to change):

```json
{
  "app_name": "tonkeeper",
  "name": "Tonkeeper",
  "image": "https://tonkeeper.com/assets/tonconnect-icon.png",
  "tondns":  "tonkeeper.ton",
  "about_url": "https://tonkeeper.com",
  "universal_url": "https://app.tonkeeper.com/ton-connect",
  "bridge": [ 
     {
        "type": "sse",
        "url": "https://bridge.tonapi.io/bridge"
     },
     {
        "type": "js",
        "key": "tonkeeper"
     }
  ],
  "platforms": ["ios", "android", "chrome", "firefox", "safari", "windows", "macos", "linux"]
}
```

#### Description
- `app_name`: string ID of your wallet. Must be equal with `ConnectEventSuccess.device.appName` and js bridge `key`
- `name`: name of your wallet. Will be displayed in the dapp.
- `image`: url to the icon of your wallet. Will be displayed in the dapp. Resolution 288×288px. On non-transparent background, without rounded corners. PNG format.
- `tondns`: (optional) will be used in the protocol later.
- `about_url`: info or landing page of your wallet. May be useful for TON newcomers.
- `universal_url`: (strictly required for `sse` bridges, optional otherwise) base part of your wallet universal url. Your link should support [Ton Connect parameters](https://github.com/ton-connect/docs/blob/main/bridge.md#universal-link)
- `bridge`: options for connectivity between the app and the wallet
    - `type="sse"`: specify the `url` of your wallet's implementation of the [HTTP bridge](https://github.com/ton-connect/docs/blob/main/bridge.md#http-bridge).
    - `type="js"`: specify the `key` through which your wallet handles [JS Bridge](https://github.com/ton-connect/docs/blob/main/bridge.md#js-bridge) connection, specify the binding for your bridge object accessible through `window`. Example: the key `"tonkeeper"` means the bridge can be accessed as `window.tonkeeper`.
- `platforms`: list of platforms on which your wallet works: mobile app "ios", "android"; desktop app "windows", "macos", "linux"; browser extension "chrome", "firefox", "safari".

If your wallet supports HTTP Bridge, you should specify `universal_url` and `bridge.type="sse"`.

If your wallet provides the JS bridge (e.g. as a browser extension), you should specify the `bridge.type="js"`.

If your wallet supports both bridges, you have to specify `universal_url` and both `bridge.type="sse"` and `bridge.type="js"`.

### How do I add my wallet?

Submit a [pull request](https://github.com/ton-connect/wallets-list/pulls) that modifies the list.

Note, that you should add your wallet **to the end of the list**.

We will review correctness of the info (obviously we want this info to be provided by the wallet’s developer) and merge it promptly.
This process may take some time.

### What is the policy?

Our goal is to represent accurate up-to-date list of all TON wallets that support TON Connect.

In the future it would be a good idea to replicate wallet's info in a TON DNS record so that this repo simply lists the wallet domain names (to filter out spam), while developers have more direct control over the wallet parameters.
