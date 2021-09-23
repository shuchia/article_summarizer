# Article Summarizer
> Article Summarizer is an asynchronous RESTful API built with Python and FastAPI. It utilizes Hugging Face transformers library to provide real-time text summarization from a given URL. 
>It also takes an excel file as an input with four columns ( Topic,Category,MM?YY,URL ) and generates reports with summaries of the URLs


## Development setup

First, install the system dependencies:
* [docker](https://docs.docker.com/)
* [docker-compose](https://docs.docker.com/compose/)
* [git](https://git-scm.com/)
* [make](https://www.gnu.org/software/make/)

Second, download the source code
```sh
https://github.com/shuchia/article_summarizer
cd article_summarizer/
```

Third, build the project image. 
```sh
make rebuild
```

## Technologies
* Python 3.8
* FastAPI 
* PostgreSQL
* Gunicorn 
* Tortoise-ORM 
* HuggingFace transformers


## File Structure
### Within the download you'll find some of the below listed directories and files:
```
├── .github
├── .gitignore
├── README.md
├── docker-compose.yml
├── makefile
├── project
│   ├── .coverage
│   ├── .coveragerc
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   ├── app
│   │   ├── __init__.py
│   │   ├── api
│   │   │   ├── __init__.py
│   │   │   ├── crud.py
│   │   │   ├── ping.py
│   │   │   └── summaries.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── main.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── pydantic.py
│   │   │   └── tortoise.py
│   │   └── summarizer.py
│   ├── db
│   │   ├── Dockerfile
│   │   └── create.sql
│   ├── entrypoint.sh
│   ├── htmlcov
│   ├── requirements-dev.txt
│   ├── requirements.txt
│   ├── setup.cfg
│   └── tests
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_ping.py
│       ├── test_summaries.py
│       └── test_summaries_unit.py
└── release.sh
```

## Release History

* 0.1.0
    * Initial release

## Acknowledgements
This project wouldn't have been possible without the excellent [Test-Driven Development with FastAPI and Docker course](https://testdriven.io/courses/tdd-fastapi/) developed by [Michael Herman](https://mherman.org/) on [testdriven.io](https://testdriven.io). You can also find a free tutorial on their blog [Developing and Testing an Asynchronous API with FastAPI and Pytest](https://testdriven.io/blog/fastapi-crud/).

## Contributing

1. Fork it (<https://github.com/shuchia/article-summarizer/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request

