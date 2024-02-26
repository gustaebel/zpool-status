test:
	@python3 test_zpool_status.py

lint:
	@pylint zpool_status.py zpool-status

clean:
	rm -rf build dist
	rm -rf *.egg-info
	rm -rf __pycache__

create-pypi-pkgs: lint test clean
	python setup.py sdist

upload: create-pypi-pkgs
	twine upload -r pypi dist/*
