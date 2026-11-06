# Upload approved TTN Finance ZIP packages here

From this folder select **Add file → Upload files**, drag your ZIP, and click **Commit changes** on the main branch.

GitHub Actions automatically checks the ZIP, imports its articles and responsive covers, updates the canonical article catalog, homepage, archive pages, related links and sitemap, verifies the site, and commits the changes. It also removes the ZIP from this queue after successful publication.

The package must include publication-manifest.json and use the same structure as the approved TTN Finance ZIP. Existing articles cannot be replaced by reuploading a ZIP. If a check fails, no publication commit is made; inspect Actions → Publish approved article ZIP.

GitHub Actions must be enabled and allowed to write repository contents. GitHub Pages must also be enabled.
