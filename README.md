# A–Z Competition Law Dictionary

A cheerful, plain-English dictionary of Australian competition law – published one
letter at a time, from A towards Z.

---

## Adding a word

1. Open **`terms.json`**.
2. Add an object to the `terms` list.
3. Commit and push.

### Word format

```json
{
  "term": "Cartel",
  "aka": "Cartel conduct",
  "emoji": "🤝",
  "definition": [
    "First paragraph.",
    "Second paragraph."
  ],
  "tags": ["conduct", "enforcement"],
  "seeAlso": ["ACCC"]
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `term` | **yes** | Name of the term, with the first letter determining the letter page. |
| `definition` | **yes** | A string, or a list of paragraphs. |
| `aka` | no | The expansion, shown as *"Otherwise known as …"*. |
| `emoji` | no | An emoji for the word. |
| `tags` | no | Topic chips at the bottom of the page, each linking to its topic page. |
| `seeAlso` | no | Other terms, by exact name. Unknown names are skipped with a warning. |
| `slug` | no | Override the URL. Defaults to a slug of `term`. |

---

## Moving to a custom domain

`baseUrl` is the only thing to change. Set it to the new address, e.g.
`https://competitionlaw.au`.

On the DNS side, point the apex at GitHub's Pages addresses (or a `www` subdomain
at `<user>.github.io`), then tick **Settings → Pages → Enforce HTTPS** once the
certificate is issued. Leave **Settings → Pages → Custom domain** filled in as
well: the build supplies the `CNAME`, but that field is what makes Pages request
the certificate.
