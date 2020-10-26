# pyGaBot
A rewrite of GaBot in python3 (minimum python 3.7 required)
As of right now it is not sharded since we're using it for a specific discord server, and because of this it is pretty much made for only running at one server at a time.

## Building
1. `pip install -r requirements.txt`
2. Make a copy of `config.template` and rename it to `config.ini`
3. Edit `config.ini` to put your Discord Token and call character in (default is `!`)
4. Run main.py with `python main.py`
