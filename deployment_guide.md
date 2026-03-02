# Deploying NYSC Chatbot to Vercel

Follow these steps to ensure a successful deployment of the frontend.

## 1. Vercel Project Settings
When you import the repository into Vercel, make sure the following settings are configured:

- **Framework Preset**: Select `Next.js`.
- **Root Directory**: Set this to `web`.
- **Build Command**: `next build` (should be default).
- **Output Directory**: Leave as **Default** (it should automatically use `.next`). Do NOT set this to `dist`.

## 2. Environment Variables
In the Vercel Dashboard, go to **Settings > Environment Variables** and add:

| Variable Name | Value |
| :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `https://nysc-chatbot-ai.onrender.com` |

## 3. Deploy
1. Go to the **Deployments** tab.
2. If the build failed previously, click **Redeploy** on the latest commit.
3. Vercel will now use the `.env.production` file I created or the environment variables you set in the dashboard.

## 4. Troubleshooting "dist" Error
If you still see the error message `The Next.js output directory "dist" was not found`:
1. Go to **Settings > General** in your Vercel project.
2. Scroll down to **Build & Development Settings**.
3. Ensure **Output Directory** is **NOT** checked/overridden. It should show `OVERRIDE` as disabled.
