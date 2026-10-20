import pytest
import time
import requests
from src.fetch_products import (
    fetch_page,
)

def test_fetch_page_retries_429_using_retry_after():
    response_200 = requests.Response()
    response_200.status_code = 200  
    response_429 = requests.Response()
    response_429.status_code = 429
    response_429.headers["Retry-After"] = "5"

    fake_responses = [
        response_429,
        response_200
    ]
    get_calls = []
    def fake_get(URL, params=None, timeout=None):
        get_calls.append(URL) 
        return fake_responses.pop(0)

    sleep_calls = []
    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    response = fetch_page(30, 30, get_function=fake_get, sleep_function=fake_sleep) 

    assert response.status_code == 200
    assert sleep_calls == [5]
    assert len(get_calls) == 2

def test_fetch_page_retries_503():
    response_500_a = requests.Response()
    response_500_a.status_code = 503
    response_500_b =requests.Response()
    response_500_b.status_code = 503
    response_200 = requests.Response()
    response_200.status_code = 200
    
    fake_responses = [
        response_500_a,
        response_500_b,
        response_200
    ]

    get_calls = []
    def fake_get(URL, params=None, timeout=None):
        get_calls.append(URL) 
        return fake_responses.pop(0)

    sleep_calls = []
    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    response = fetch_page(30, 30, get_function=fake_get, sleep_function=fake_sleep) 

    assert response.status_code == 200
    assert sleep_calls == [1, 2]
    assert len(get_calls) == 3

def test_fetch_page_timeout():
    response_timeout = requests.exceptions.Timeout()
    response_200 = requests.Response()
    response_200.status_code = 200

    fake_responses = [
    response_timeout,
    response_timeout,
    response_200
    ]

    get_calls = []
    def fake_get(URL, params=None, timeout=None):
        get_calls.append(URL)

        result = fake_responses.pop(0)

        if isinstance(result, Exception):
            raise result

        return result
    
    sleep_calls = []
    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    response = fetch_page(30, 30, get_function=fake_get, sleep_function=fake_sleep) 

    assert response.status_code == 200
    assert sleep_calls == [1, 2]
    assert len(get_calls) == 3

def test_fetch_page_404_error():
    response_404 = requests.Response()
    response_404.status_code = 404
    response_500 = requests.Response()
    response_500.status_code = 503
    response_200 = requests.Response()
    response_200.status_code = 200

    fake_responses = [
        response_404,
        response_500,
        response_200
    ]
    get_calls = []
    def fake_get(URL, params=None, timeout=None):
        get_calls.append(URL) 
        return fake_responses.pop(0)

    sleep_calls = []
    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    
    with pytest.raises(requests.exceptions.HTTPError):
        fetch_page(30, 30, get_function=fake_get, sleep_function=fake_sleep)

    assert len(get_calls) == 1
    assert sleep_calls == []

    
def test_fetch_page_raises_after_503_retries_exhausted():
    response_503_a = requests.Response()
    response_503_a.status_code = 503
    response_503_b =requests.Response()
    response_503_b.status_code = 503
    response_503_c = requests.Response()
    response_503_c.status_code = 503
    
    fake_responses = [
        response_503_a,
        response_503_b,
        response_503_c
    ]

    get_calls = []
    def fake_get(URL, params=None, timeout=None):
        get_calls.append(URL) 
        return fake_responses.pop(0)

    sleep_calls = []
    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    with pytest.raises(requests.exceptions.HTTPError):
        fetch_page(30, 30, get_function=fake_get, sleep_function=fake_sleep)

    assert sleep_calls == [1, 2]
    assert len(get_calls) == 3
