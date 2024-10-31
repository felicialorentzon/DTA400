# DTA400

## Setup

For both projects, prepare your environment with this:

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Carwash

To run:

```sh
python car_wash.py
```

## Phone service

To run full simulation:

```sh
cd phone_service
./generate_data.sh
```

To run a single instance:

```sh
python phone_service/phone_booth.py <number_of_phones>
```

Where `<number_of_phones>` must be an integer and expected to
be greater than 0.

### CI

The phone service project runs with GitHub Actions and generates
graphs for every push. These are accessible from the `Actions` tab.
