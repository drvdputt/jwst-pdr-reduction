poetry install
# needed for NSClean, but conflicts with jwst because pandas needs newer numpy, and jwst needs
# older numpy (because it needs older scipy)
poetry run pip install pandas
