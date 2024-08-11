# Groq-Storyteller

Groq-Storyteller is a self-hosted AI story generator made with Python and Groq API. Requires Python 3.9 or above, and an Internet connection. You will also need your Groq API key.

## Installation

- Assuming you have Python, use the following command first:

```bash
pip install -r requirements.txt
```

- Create a .flaskenv file and add the following variables:

```
FLASK_APP=everglen_web.py
GROQ_API_KEY=(please use your Groq API key)
```

## Usage

* When not running on a WSGI server, use the following command:

```bash
flask run --host=0.0.0.0
```

* Open a web browser and enter the IP address and port number shown on the terminal, e.g. 192.168.1.13:5000

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.