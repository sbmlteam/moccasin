'''
network_utils: network utilities used by MOCCASIN Interface
'''

def have_network():
    '''Connects somewhere to test if a network is available.'''
    import requests
    try:
        _ = requests.get('http://www.google.com', timeout=5)
        return True
    except requests.ConnectionError:
        return False
