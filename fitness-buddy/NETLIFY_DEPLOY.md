# Deploy Fitness Buddy on Netlify

## Quickest route: upload the ready-made folder

1. Extract `Fitness-Buddy-Starter.zip`.
2. Open `fitness-buddy`. Locate the **`netlify-site`** folder; it contains `index.html`, `app.js`, `store.js`, `style.css`, and `thank-you.html`.
3. Sign in to your Netlify account and open https://app.netlify.com/drop.
4. Drag **`netlify-site`** into the upload area. Upload this folder, not the Python project or its old `static` folder.
5. Open the URL Netlify provides. Partner matching and demo meetups work immediately; no build or Python process is needed.

## Activate collection of real pilot interest

The published page includes an HTML form named **`pilot-interest`**, with consent and a spam-trap field.

1. In the Netlify project's **Forms** area, enable **form detection** if it is not already enabled.
2. Deploy the same `netlify-site` folder again so Netlify processes the form.
3. Confirm `pilot-interest` appears in the Forms area.
4. Submit one test entry on the live URL. Confirm it appears under that form in your Netlify project. If it is filtered, check spam submissions as well.
5. Delete the test entry before reporting real customer-validation numbers.

Submission notification emails require separate configuration in Netlify. The app does not automatically email participants. A successful form submission uses `/thank-you.html`. Merely opening that page is not evidence that a signup was captured: verify the record in Forms.

If the form is absent, confirm detection is enabled and redeploy. If submission returns 404, check that the exact form markup is deployed and the form is detected. The form uses native HTML POST; Netlify processes it on the hosted site. Local preview blocks submission and explains that signup requires deployment.

## What is saved where

| Information | Storage | Who sees it |
| --- | --- | --- |
| Demo profile preferences | Browser localStorage | That browser on that site/domain |
| Created demo meetups and attendance | Browser localStorage | That browser on that site/domain |
| Fictional partners | Static application code | All visitors |
| Consented pilot-interest email | Netlify Forms, after detection and deployment | People with access to your Netlify project |

This is an interactive validation prototype. Visitors cannot see one another's profiles or meetups. Browser data does not sync across devices or domains, can be cleared by the visitor, and may be blocked by browser settings. The original Python/SQLite data is not migrated into the website. Simultaneous demo edits across tabs are not a multi-user database.

There is no public signup counter: raw form submissions are not automatically unique or verified. When evaluating demand, exclude tests/spam and deduplicate email addresses before reporting participant counts.

## Deploy from a Git repository instead

If the repository root is the extracted `fitness-buddy` folder:

- Base directory: leave empty.
- Build command: leave empty.
- Publish directory: `netlify-site`.

The root `netlify.toml` supplies the publish directory. If your repository contains an enclosing folder, set the base directory to `fitness-buddy`. If only the contents of `netlify-site` are in the repository root, use publish directory `.`; the config inside that folder supports this layout.

Only `netlify-site` needs to be published. There are no server functions, package installations, secrets, or environment variables for this version.

## Run the new smoke checks locally

With Node.js installed, from `fitness-buddy`:

```powershell
node --test tests/test_netlify.cjs
```

These 15 checks use Node's built-in test runner and require no npm packages. They exercise persistence, matching, creating/joining/leaving meetups, invalid input, full and expired meetups, blocked/corrupt storage, and deployment assets/form markup. They do not send real form submissions.

For local visual preview, from `fitness-buddy`:

```powershell
py -m http.server 8080 --bind 127.0.0.1 --directory netlify-site
```

Open http://127.0.0.1:8080. Python here only serves static files for preview; it is not used on Netlify. Do not open `index.html` directly from your filesystem.

The older `tests/browser_smoke.cjs` targets the original Python app and its local signup counter. It is not a Netlify test suite.

## Five live smoke checks after deployment

1. Load the public URL. Expect four fictional partner cards and no missing assets.
2. Save Running / Weekend mornings / Intermediate / Downtown. Sam should appear first with 4/4 matching preferences. Reload and verify those preferences remain.
3. Create a future meetup, leave, and rejoin. Reload and check attendance remains saved. Open a private browser window: it should have a fresh demo rather than your saved meetup.
4. Submit the consented pilot-interest form and confirm receipt in **Netlify Forms → pilot-interest**. This is the required end-to-end collection check.
5. Open the page on a phone and check that forms and buttons are usable.

The site has not been deployed to your Netlify account by this update. Actual Netlify form receipt and browser rendering are still deployment checks for you to complete.

Official references, checked October 22, 2026:

- https://docs.netlify.com/deploy/create-deploys/
- https://docs.netlify.com/manage/forms/setup/
