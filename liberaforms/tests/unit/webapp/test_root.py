from liberaforms.tests.unit.webapp import client

def test_landing(client):
    landing = client.get("/")
    assert landing.status_code == 200
    html = landing.data.decode()
    assert '<a class="navbar-brand" href="/"><img src="/favicon.png" /></a>' in html
