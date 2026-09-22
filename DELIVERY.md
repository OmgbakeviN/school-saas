# BE WISE School — HOTFIX Dashboard PDF download handler

The previous Dashboard Statistics PDF package inserted
`downloadStatisticsPdf` inside the small `StatCard` component instead of
inside `DashboardAnalytics`.

That caused:

```text
ReferenceError: downloadStatisticsPdf is not defined
```

when the main dashboard tried to render its download button.

This hotfix moves the handler into the correct component scope.

## Extract

Extract directly into:

```text
C:\Users\dell\school saas\
```

It overwrites only:

```text
frontend\src\modules\tenant\DashboardAnalytics.jsx
```

## Restart frontend

```powershell
cd "C:\Users\dell\school saas\frontend"
npm run dev
```

If Vite is already running, a hard refresh is normally enough.

## Backend PDF endpoint

The previous package already added:

```text
GET /api/tenant/dashboard/statistics.pdf
GET /api/tenant/dashboard/classrooms/<id>/statistics.pdf
```

If a 404 still appears after this UI fix, inspect the exact URL in the browser
Network panel. The React crash itself is fixed by this package.
