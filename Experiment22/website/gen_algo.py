import csv, time
from collections import namedtuple
from functools import partial
from random import choices, randint, randrange, random
from typing import List, Callable, Tuple

# Define the namedtuple
Thing = namedtuple('Thing', ['name', 'rating', 'price'])

# Define the CSV file paths
csv_file_path = 'C:/Users/Adrian/Desktop/HTML Guide 2/Capstone/Experiment1/csvs/things.csv'
catering = 'C:/Users/Adrian/Desktop/HTML Guide 2/Capstone/Experiment1/csvs_deluxe/Catering.csv'
church = 'C:/Users/Adrian/Desktop/HTML Guide 2/Capstone/Experiment1/csvs_deluxe/Church.csv'
event_stylist = 'C:/Users/Adrian/Desktop/HTML Guide 2/Capstone/Experiment1/csvs_deluxe/Event_Stylist.csv'
events_place = 'C:/Users/Adrian/Desktop/HTML Guide 2/Capstone/Experiment1/csvs_deluxe/Events_Place.csv'
lights_and_sounds = 'C:/Users/Adrian/Desktop/HTML Guide 2/Capstone/Experiment1/csvs_deluxe/Lights_and_Sounds.csv'

# Initialize lists to store namedtuples
things_list = []
catering_arr = []
church_arr = []
event_stylist_arr = []
events_place_arr = []
lights_and_sounds_arr =[]

# Open the CSV file and load data into namedtuples
with open(csv_file_path, mode='r', newline='') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        thing = Thing(name=row['name'], rating=int(row['rating']), price=float(row['price']))
        things_list.append(thing)

with open(catering, mode='r', newline='') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        thing = Thing(name=row['name'], rating=int(row['rating']), price=float(row['price']))
        catering_arr.append(thing)

with open(church, mode='r', newline='') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        thing = Thing(name=row['name'], rating=int(row['rating']), price=float(row['price']))
        church_arr.append(thing)

with open(event_stylist, mode='r', newline='') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        thing = Thing(name=row['name'], rating=int(row['rating']), price=float(row['price']))
        event_stylist_arr.append(thing)

with open(events_place, mode='r', newline='') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        thing = Thing(name=row['name'], rating=int(row['rating']), price=float(row['price']))
        events_place_arr.append(thing)

with open(lights_and_sounds, mode='r', newline='') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        thing = Thing(name=row['name'], rating=int(row['rating']), price=float(row['price']))
        lights_and_sounds_arr.append(thing)

# Update the code to include the namedtuples
new_things = things_list
catering1 = catering_arr
church1 = church_arr
event_stylist1 = event_stylist_arr
events_place1 = events_place_arr
lights_and_sounds1 = lights_and_sounds_arr

Genome = List[int]
Population = List[Genome]
FitnessFunc = Callable[[Genome], int]
PopulateFunc = Callable[[], Population]
SelectionFunc = Callable[[Population, FitnessFunc], Tuple[Genome, Genome]]
CrossoverFunc = Callable[[Genome, Genome], Tuple[Genome, Genome]]
MutationFunc = Callable[[Genome, int, float], Genome]

# Genome and population generation functions
def generate_genome(length: int) -> Genome:
    return choices([0, 1], k=length)

def generate_population(size: int, genome_length: int) -> Population:
    return [generate_genome(genome_length) for _ in range(size)]

def fitness(genome: Genome, things_list: List[Thing], price_limit: int) -> int:
    if len(genome) != len(things_list):
        raise ValueError("Genome and things list must be of the same length")

    price = 0
    rating = 0

    for i, thing in enumerate(things_list):
        if genome[i] == 1:
            price += thing.price
            rating += thing.rating

    if price == 0:
        return 0  # Penalize genomes with zero price if necessary

    if price > price_limit:
        return 0  # Penalize genomes that exceed the price limit
    
    return rating

# Selection, crossover, and mutation functions
def selection_pair(population: Population, fitness_func: FitnessFunc) -> Population:
    return choices(
        population=population,
        weights=[fitness_func(genome) for genome in population],
        k=2
    )

def single_point_crossover(a: Genome, b: Genome) -> Tuple[Genome, Genome]:
    if len(a) != len(b):
        raise ValueError("Genomes a and b must be of the same length")

    length = len(a)
    if length < 2:
        return a, b

    p = randint(1, length - 1)
    return a[0:p] + b[p:], b[0:p] + a[p:]

def mutation(genome: Genome, num: int = 1, probability: float = 0.1) -> Genome:
    for _ in range(num):
        index = randrange(len(genome))
        genome[index] = genome[index] if random() > probability else abs(genome[index] - 1)
    return genome

def run_evolution(
        populate_func: PopulateFunc,
        fitness_func: FitnessFunc,
        fitness_limit: int,
        selection_func: SelectionFunc = selection_pair,
        crossover_func: CrossoverFunc = single_point_crossover,
        mutation_func: MutationFunc = mutation,
        generation_limit: int = 200
) -> Tuple[Population, int]:
    population = populate_func()

    for i in range(generation_limit):
        # Sort population by fitness
        population = sorted(
            population,
            key=lambda genome: fitness_func(genome),
            reverse=True
        )

        # Check if the best genome has reached the fitness limit
        best_fitness = fitness_func(population[0])
        if best_fitness >= fitness_limit:
            break

        next_generation = population[0:2]  # Elitism: carry over the best 2

        # Generate the rest of the next generation
        for j in range(int(len(population) / 2) - 1):
            parents = selection_func(population, fitness_func)
            offspring_a, offspring_b = crossover_func(parents[0], parents[1])
            offspring_a = mutation_func(offspring_a)
            offspring_b = mutation_func(offspring_b)
            next_generation += [offspring_a, offspring_b]

        population = next_generation

    return population, i

# Helper function to convert genome to list of things
def genome_to_things(genome: Genome, things_list: List[Thing]) -> List[Thing]:
    result = []
    for i, thing in enumerate(things_list):
        if genome[i] == 1:
            result.append(thing.name)
    return result

# # Parameters for price limit of 1000
# price_limit = 5000
# fitness_limit = 500  # Adjust fitness limit to reflect more restrictive price limit
# population_size = 20  # Increase population size for better exploration
# generation_limit = 200  # Increase generation limit for thorough search

# start = time.time()
# population, generations = run_evolution(
#     populate_func=partial(
#         generate_population, size=population_size, genome_length=len(things_list)
#     ),
#     fitness_func=partial(
#         fitness, things_list=things_list, price_limit=price_limit
#     ),
#     fitness_limit=fitness_limit,
#     generation_limit=generation_limit
# )
# end = time.time()

# print(f"number of generations: {generations} ")
# print(f"time: {end - start}s")
# print(f"best solution: {genome_to_things(population[0], things_list)}")

# best_answers = genome_to_things(population[0], things_list)
# new_answer = ['MEEEEEEEE']
# best_answers = best_answers + new_answer
# print(best_answers)

# for items in best_answers:
#     print(*items, sep ="\n")

# for items in photographer1:
#     print(*items)
