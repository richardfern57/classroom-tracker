import setuptools

setuptools.setup(
    name='classroom-tracker',
    version='0.0.1',
    packages=setuptools.find_packages(),
    install_requires=[
        'pandas>=1.0.3',
        'google-api-python-client>=1.8.0',
        'google-auth-oauthlib>=0.4.1']
)
