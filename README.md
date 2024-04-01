# CYBer INTelligence

Yet another tool to manage news feed

- manage multiple projects
- manage feeds for each projet
- get articles from Atom/RSS feeds
- bookmarks articles and export to PDF

## Requirements

Following software components are required

- No-SQL database `mongodb` from https://www.mongodb.com/
- Management GUI `mongo-express` from https://github.com/mongo-express/mongo-express/
- CybInt components from https://github.com/vmapps/cybint

Following Python packages are required

- `colored` from https://dslackw.gitlab.io/colored/colored/
- `feedparser` from https://github.com/kurtmckee/feedparser
- `flask` from https://flask.palletsprojects.com/
- `nltk` from https://www.nltk.org/
- `pymongo` from https://github.com/mongodb/mongo-python-driver
- `pyyaml` from https://pyyaml.org/

Following NTLK packages are required

- `punkt`
- `averaged_perceptron_tagger`

They could be installed using following commands

```sh
python3 -m nltk.downloader -d ./nltk_data punkt
python3 -m nltk.downloader -d ./nltk_data averaged_perceptron_tagger
```

## Configuration

Feeds should be declared in folder `config/projects/<project>.feeds`

Each `<project>.feeds` file should contain one feed per line using following format

```
<feed-id>,<feed-name>,<feed-url>
```

Example

```
didierstevens,Didier Stevens Blog,https://blog.didierstevens.com/feed/
datasecuritybreach,Data Security Breach,https://datasecuritybreach.fr/feed/
#another-feed,Disabled Feed,https://route.tonowhere.com/feed/
```

## Install with Docker

Build the CybInt image

```sh
docker build -t cybint .
```

Run all components with docker compose

```sh
docker compose up -d
```

## Screenshots

![cybint-feeds](https://github.com/vmapps/cybint/blob/main/docs/cybint-feeds.png?raw=true)

![cybint-articles](https://github.com/vmapps/cybint/blob/main/docs/cybint-articles.png?raw=true)

![cybint-bookmarks](https://github.com/vmapps/cybint/blob/main/docs/cybint-bookmarks.png?raw=true)

![cybint-keywords](https://github.com/vmapps/cybint/blob/main/docs/cybint-keywords.png?raw=true)
