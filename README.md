# commute-times
Uses Google's Directions API to calculate commute times to/from potential homes

## Usage:

There are two main ways to use these tools.  In either case, you must first setup
your configuration file and create an API key.

### Setup:

First, create a Google API Key and enable both the Directions and Maps JavaScript 
APIs.  You'll also need to enable a billing account, but don't worry -- you get 
a $300 credit to start with, and the Maps API give you an additional $200 credit
each month.  Even in debugging, testing, and usage, I never went through more than
about $30 of that monthly credit.

Second, create your configuration file.  It should look like:

```
timezone: <timezone, e.g. America/San_Francisco, or don't include to use local timezone>
api_key: <Google API key>
commutes:
    <person 1 name>:
        address:  <person 1 work address>
        arrival_hour: <hour person 1 arrives at work (24-hour; e.g. 9)
        arrival_minute: <minute person 1 arrives at work>
        departure_hour: <hour person 1 departs work (24-hour; e.g. 17)
        departure_minute: <minute person 1 departs work>
    <person 2 name>:
        ...
    ...
```

You can either save this in the same directory as the scripts as 
`private_info.txt`, or you can give it any name you want and pass it to 
each of the scripts as `-c <path/to/file>`.

#### Per-address:

Simply call `python commute_times.py` with the address you want to calculate 
commute times relative to (i.e. the address of a house/apartment for sale/rent).  
Use `python commute_times.py --help` to see the available options, which include
the period of time over which the commute will be calculated, which model to 
print the final summary for, and the path to the configuration filename.

The script will use the Directions API to query for the right time to leave 
in the morning and the amount of time it'll take to get home in the afternoon
for each person given in the configuration file.  It'll do this for all three
models, then print out a table for each person of best and worst case scenarios
for each traffic model, then finally print a summary of the average guess from 
the selected `return_model`.

#### Grid search:

There are also tools to create a grid of commute times to and from work for each
person within some lat/lng boundaries.  Note that this will take a good bit of 
time, especially for the commute to work where the departure time is uncertain
(in particular, this is the function that will end up costing you money, if 
anything does), so don't go too crazy with the number of points right away.

First, you're going to use `build_commute_grid.py` to query commute times from 
a grid of latitute and longitute points, the results of which will be saved to a
pickle file given by the sole required argument.  However, the limits of the 
rectangle (given by `northern/southern/eastern/western_limit`) and the number 
of points (`npts`) are both important optional arguments.  You should also set 
the name of the state that you want to bound the points within (usually to 
separate land from water), or you can set to `None` (as a string) to skip this 
step (e.g. for a completely land area).  Once you've set all your args (perferably 
with a low `npts` to start), fire off the script and wait for it to finish.

Next you'll want to plot the result.  Call `plot_commute_grid.py` to get a sense
of the arguments.  There are two required args, the name of the pickle file that
you created with `build_commute_grid.py`, and the name of the output file you want
to create (will be an html webpage).  Most of the optional arguments are 
self-explanatory, except perhaps `center_lat` and `center_lng` -- these set the 
initial center of the map.  If these (independently) are aren't set as valid 
floats, then the code will default to the center of the grid.

Once you're satisfied with your grid and think everything is working ok, go ahead 
and up the number of points in your search, and have fun!







