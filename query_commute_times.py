#!/usr/bin/env python3

import requests
from datetime import datetime, timedelta


class CommuteTimesClass:
    def __init__(self, key):
        self.base = "https://maps.googleapis.com/maps/api/directions/json?"
        self.KEY = key

    def escaped_string(self, string):
        return '+'.join(string.replace(',','').split())

    def datetime_to_unix(self, dt):
        return str(int(dt.timestamp()))
        # return dt.strftime('%s')

    def build_url(self, departure_address, arrival_address, departure_time=None, arrival_time=None, traffic_model='best_guess'):
        if not len(self.KEY):
            raise ValueError("Must provide a non-empty API key")

        if arrival_time is not None:
            assert departure_time is None
        if departure_time is not None:
            assert arrival_time is None

        url = self.base + "origin=" + self.escaped_string(departure_address)
        url += "&destination=" + self.escaped_string(arrival_address)
        if departure_time is not None:
            url += "&departure_time=" + self.datetime_to_unix(departure_time)
            url += "&traffic_model="+traffic_model
        if arrival_time is not None:
            url += "&arrival_time=" + self.datetime_to_unix(arrival_time)

        url += "&key="+self.KEY
        return url

    def get_estimated_time(self, departure_address, arrival_address, **kwargs):
        url = self.build_url(departure_address, arrival_address, **kwargs)
        res = requests.get(url)
        return res.json()['routes'][0]['legs'][0]['duration_in_traffic']['value']/60

    def find_depart_time(self, departure_address, arrival_address, target_arrival_time, 
        guess=45, early_tolerance=7, late_tolerance=0, initial_step=20, 
        min_step=5, max_calls=8, **kwargs):
        """
        search to find the right time to leave to get to somewhere by a certain time

        target_arrival_time should be a datetime.datetime object.
        all other times (guess, early_tolerance, late_tolerance) should be
            integer minutes.  early_tolerance is how early you're 
            willing to be there; late_tolerance is how late you're
            willing to be there (both positive)

        """
        def get_departure_from_guess(this_guess):
            dt = timedelta(minutes=this_guess)
            return target_arrival_time - dt

        def get_difference(this_guess):
            this_time = get_departure_from_guess(this_guess)
            travel_time = self.get_estimated_time(departure_address, 
                arrival_address, departure_time=this_time, **kwargs)

            arrival_time = this_time + timedelta(minutes=travel_time)

            ## if positive, then target_arrival_time is later, which means
            ## we get there earlier than we want, which isn't ideal but is ok.

            ## if negative, then we're getting there late, which isn't ok
            # print(f"guess = {guess}, departure = {this_time}," + 
            #       f" travel = {travel_time}, arrival = {arrival_time}," + 
            #       f" target = {target_arrival_time}")

            return (target_arrival_time - arrival_time).total_seconds()/60

        difference = get_difference(guess)

        step = initial_step
        calls = 1
        while (difference < -1*abs(late_tolerance)) or (difference > early_tolerance):
            # print(f"difference = {difference}\n\n")
            if difference > 0:
                ## target is greater than actual => we got there too early
                ## so leave later, which means use a smaller guess
                guess = guess - step
            else:
                ## target is less than actual, so we got there too late =>  leave earlier
                guess = guess + step
            difference = get_difference(guess)
            step = max(min_step, 0.75*step)

            calls += 1
            if calls > max_calls:
                print(f"Too many calls -- last difference is {difference}")
                break

        return get_departure_from_guess(guess)


    def find_commute_to_work_length(self, departure_address, arrival_address, 
        target_arrival_time, **kwargs):

        departure_time = self.find_depart_time(departure_address, arrival_address, 
            target_arrival_time, **kwargs)

        ## now the length is target_arrival_time - departure_address
        transit_time = (target_arrival_time - departure_time).total_seconds()/60
        return transit_time

    def pretty_print(self, towork, tohome, local_info):
        def subprint(subtowork, subtohome, key):
            def subsubprint(dictionary):        
                pess = dictionary['pessimistic']
                opt = dictionary['optimistic']
                best = dictionary['best_guess']
                print('Pessimistic:'.ljust(20, ' ') + f' {min(pess):.0f} -- {max(pess):.0f}')
                print('Optimistic:'.ljust(20, ' ') + f' {min(opt):.0f} -- {max(opt):.0f}')
                print('Best-guess:'.ljust(20, ' ') + f' {min(best):.0f} -- {max(best):.0f}')
                print('Best/wost case:'.ljust(20, ' ') + f' {min(opt):.0f} -- {max(pess):.0f}')

            label = f"{key}'s commute"
            lablength = len(label)
            dots = '-'*((80 - lablength - 2)//2)
            print()
            print(dots+' '+label+' '+dots)
            towork_string = f"Commute to work (arriving by {local_info[key]['arrival_hour'] % 12}:{str(local_info[key]['arrival_minute']).zfill(2)})"
            print(towork_string)
            print('-'*len(towork_string))
            subsubprint(subtowork)
            print()
            tohome_string = f"Commute home (leaving at {local_info[key]['departure_hour'] % 12}:{str(local_info[key]['departure_minute']).zfill(2)})"
            print(tohome_string)
            print('-'*len(tohome_string))
            subsubprint(subtohome)
            print('-'*80)

        for key in towork:
            subprint(towork[key], tohome[key], key)

def main():
    from collections import defaultdict
    from argparse import ArgumentParser
    from tqdm import tqdm
    import os
    import yaml
    import pytz

    basedir = os.path.realpath(__file__).rsplit('/', 1)[0]

    parser = ArgumentParser()
    parser.add_argument("address", help="Address to calculate commutes to/from")
    parser.add_argument('-p', '--private', help="Config file with private info", default=basedir+'/private_info.txt', dest='pifile')
    parser.add_argument('-k', '--keyfile', help="One-line text file with Google API key", default=basedir+'/api_key', dest='keyfile')
    parser.add_argument('--key', default=None, help="Google API key (over-rides -k option)", dest='key')
    parser.add_argument('--year', default=2019, type=int)
    parser.add_argument('--month', default=8, type=int)
    parser.add_argument('--first_day', default=6, help="Start on Aug 6 2019, a Tuesday", type=int)
    parser.add_argument('--ndays', default=4, help="How many days to run for (i.e. work week)", type=int)

    args = parser.parse_args()

    ### parse our inputs:
    if args.key is None:
        with open(args.keyfile, 'r') as f:
            key = f.readline()
    else:
        key = args.key

    with open(args.pifile, 'r') as f:
        local_info = yaml.load(f)

    if 'timezone' in local_info:
        timezone = pytz.timezone(local_info.pop('timezone'))
    else:
        import tzlocal
        timezone = tzlocal.get_localzone()

    towork = defaultdict(lambda: defaultdict(list))
    tohome = defaultdict(lambda: defaultdict(list))

    CommuteTimes = CommuteTimesClass(key=key)

    for (name, info) in tqdm(local_info.items(), desc="People completed", position=0):
        for day in tqdm(range(args.first_day, args.first_day + args.ndays), desc='Days', position=1):
            for model in tqdm(['optimistic', 'pessimistic', 'best_guess'], desc="model", position=2):
                ## to work:
                time = timezone.localize(datetime(args.year, args.month, day, 
                    hour=info['arrival_hour'], minute=info['arrival_minute']))
                towork[name][model].append(CommuteTimes.find_commute_to_work_length(args.address, info['address'], time, traffic_model=model))

                ## to home
                time = timezone.localize(datetime(args.year, args.month, day, 
                    hour=info['departure_hour'], minute=info['departure_minute']))
                tohome[name][model].append(CommuteTimes.get_estimated_time(info['address'], args.address, 
                    departure_time=time, traffic_model=model))

    string = f"Commutes from {args.address}"
    dots = "="*((80 - len(string))//2 - 2)
    print(dots + ' ' + string + ' ' + dots)
    CommuteTimes.pretty_print(towork, tohome, local_info)

if __name__ == "__main__":
    main()
