# BRYME Media

BRYME Media is the extracted sports and entertainment archive from the main BRYME repository.

It contains:

- sports pages, match pages, reports and source datasets;
- movie, series and anime title interfaces;
- original entertainment articles;
- genre/year discovery routes;
- trailer and catalogue data; and
- the media assets and historical build scripts required to preserve the work.

## Migration status

Every page is deliberately `noindex,follow` until a final host is deployed and the following are approved:

1. permanent domain and canonical host;
2. sports-data source rights and update integrity;
3. title-image and other media rights;
4. current, accurate metadata;
5. a media-specific index allowlist; and
6. production HTTP behavior.

Do not remove `noindex` in bulk.

## Build

```bash
npm run build
npm test
npm start
```

`npm run build` applies the media navigation and forest-green compatibility layer without rewriting article bodies.

## Relationship to BRYME

The main BRYME publication now focuses on jobs, paid writing, opportunities and practical guides. This repository is maintained separately so Search and users receive a clear topical purpose from each publication.
