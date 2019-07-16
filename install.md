

# Install

Create a python venv.

Python3 on host
```
apt-get install python3-venv
python3 -m venv /opt/venv
```

Or if you have old python2 on your host
```
apt-get install virtualenv
virtualenv /opt/venv --python=python3
```


```
source /opt/venv/bin/activate
pip install flask
pip install flask_script
pip install Markdown
pip install flask_babel
pip install validate_email
pip install password_strength
pip install passlib

```

```
git clone https://gitlab.com/lleialtec/gngforms.git
cd /opt/gngforms
cp config.example.cfg config.cfg
```

Edit `/opt/gngforms/config.cfg`
