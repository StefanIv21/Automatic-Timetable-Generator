from __future__ import annotations
from copy import deepcopy as copy
import os
import random
from utils import *
import queue
from time import time
from math import sqrt, log
import numpy as np
from queue import Queue


def check_interval(interval):
    check = 0
    if "!" in interval:
        check = 1
        interval = interval[1:]
    format_interval = interval.split('-')
    if check == 1:
        return [f"!{i}-{i+2}" for i in range(int(format_interval[0]),int(format_interval[1]),2)]
    return [f"{i}-{i+2}" for i in range(int(format_interval[0]),int(format_interval[1]),2)]

def format_interval(interval):
    if "!" in interval:
        interval = interval[1:]
    format_interval = interval.split('-')
    format_interval = (int(format_interval[0]),int(format_interval[1]))
    return format_interval

def check_pauza(orar,day,interval,teacher,hours):
    list_intervals = []
    nr = 0
    for interval in orar[day].keys():
        for  room in  orar[day][interval].keys():
            value = orar[day][interval][room]
            if value is not None and value[0] == teacher:
                list_intervals.append(interval)
    for i in range(0,len(list_intervals)-1):
        if list_intervals[i+1][0] - list_intervals[i][1] > hours:
            nr += 1
    return nr

class State:
    def __init__(self, orar, nconflicts,max_hoursT,hours_course):
        self.orar = orar
        self.nconflicts = nconflicts
        self.max_hoursT = max_hoursT
        self.hours_course = hours_course

    def apply_move(self,day,interval,course,room,day_mod,interval_mod,profesor):
        nconflicts = copy(self.nconflicts)
        max_hoursT = copy(self.max_hoursT)
        hours_course = copy(self.hours_course)
        new_orar = copy(self.orar)
        if "!" in day:
            nconflicts += 10
        if "!" in interval:
            nconflicts += 10
        ok = 0
        for value in new_orar[day_mod][interval_mod].values(): 
            if value is not None and value[0] == profesor:
                ok = 1
                break
        if ok == 1:
            return 
        if max_hoursT[profesor] == 7:
            return 
        new_orar[day_mod][interval_mod][room] = (profesor, course)
        if "Pauza" in timetabel_teacher[profesor]:
            hours = timetabel_teacher[profesor]["Pauza"]
            nconflicts += check_pauza(new_orar,day_mod,interval_mod,profesor,hours)
        max_hoursT[profesor] += 1
        hours_course[course] -= dict_file['Sali'][room]['Capacitate']
        state = State(new_orar,nconflicts,max_hoursT,hours_course)
        return ((state,room,day_mod,profesor))
        
                
    def get_next_states(self, course):
        results = []
        state = self
        for room in dict_file['Sali']:
            if course not in dict_file['Sali'][room]['Materii']:
                continue    
            for profesor in courses[course].keys():
                domeniu = courses[course][profesor]
                for day in domeniu['Zi']:
                    day_mod = day
                    if "!" in day:
                        day_mod = day[1:]
                    for interval in domeniu['Interval']:
                        interval_mod = format_interval(interval)
                        if self.orar[day_mod][interval_mod][room] == None:
                            result = state.apply_move(day,interval,course,room,day_mod,interval_mod,profesor)
                            if result is not None:
                                results.append(result)
        return results

    def conflicts(self):
        return self.nconflicts
    
    def room_nr_courses(self,sala):
        return len(dict_file['Sali'][sala]['Materii'])

    def is_final(self):
        return self.nconflicts == 0
    
    def check_final_state_course(self,course):
        return self.hours_course[course] <= 0
    
    
    def clone(self) -> State:
        return State(copy(self.orar),copy(self.nconflicts),copy(self.max_hoursT),copy(self.hours_course))

def hill_climbing(initial: State, priority_queue: queue.PriorityQueue, max_iters: int = 1000):
    iters, states = 0, 0
    state = initial
    while not priority_queue.empty():
        course = priority_queue.get()
        while iters < max_iters:
            iters += 1
            next_states = state.get_next_states(course)
            states += len(next_states)
            if len(next_states) == 0:
                break   
            best_state = min(next_states, key=lambda x: (x[0].nconflicts,
                                                         x[0].hours_course[course],
                                                         x[0].room_nr_courses(x[1]),
                                                         days_restriction[x[2]]
                                                        +len(teacher_interval[x[3]]['C_Zi'])+len(teacher_interval[x[3]]['C_Interval'])))
            state = best_state[0]
            if state.hours_course[course] <= 0:
                break
    return state.is_final(), state, iters, states

N = 'N'
Q = 'Q'
STATE = 'state'
PARENT = 'parent'
ACTIONS = 'actions'

def init_node(state, parent = None):
    return {N: 0, Q: 0, STATE: state, PARENT: parent, ACTIONS: {}}

CP = 1.0 / sqrt(2.0)
def softmax(x: np.array) -> float:
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

def select_action(node, c = CP):
    N_node = node[N]
    A_node = node[ACTIONS]
    max_UCB = -1
    action = None
    for children in A_node:
        N_a = A_node[children][N]
        Q_a = A_node[children][Q]
        UCB = Q_a / N_a + c * sqrt(2 * log(N_node) / N_a)
        if UCB > max_UCB:
            max_UCB = UCB
            action = children
    return action

def mcts(state0, budget,tree, course):
    tree = tree if tree else init_node(state0)
    states = 0
    for x in range(budget):
        node = tree
        state = state0
        list_neigh = state.get_next_states(course)
        if x == 0:
            states += len(list_neigh)
        while state.check_final_state_course(course) == False and all([list_neigh.index(a) in node[ACTIONS] for a in list_neigh]):
            action = select_action(node)
            state = node[ACTIONS][action][STATE]
            list_neigh = state.get_next_states(course)
            if x == 0:
                states += len(list_neigh)
            node = node[ACTIONS][action]
        if list_neigh == []:
            break
        scores = [(s[0].conflicts()*10 + 
                       s[0].hours_course[course] +
                        s[0].room_nr_courses(s[1]) +
                        days_restriction[s[2]] +
                        len(teacher_interval[s[3]]['C_Zi']) +
                        len(teacher_interval[s[3]]['C_Interval'])
                         ) for s in list_neigh]
        if state.check_final_state_course(course) == False:
            index = np.random.choice(len(list_neigh), p=softmax(-np.array(scores)))
            action = list_neigh[index]
            state = action[0]
            node = init_node(state, node)
            node[PARENT][ACTIONS][index] = node
        state = node[STATE]
        while state.check_final_state_course(course) == False:
            list_neigh = state.get_next_states(course)
            if x == 0:
                states += len(list_neigh)
            scores = [(s[0].conflicts()*10 + 
                       s[0].hours_course[course] +
                        s[0].room_nr_courses(s[1]) +
                        days_restriction[s[2]] +
                        len(teacher_interval[s[3]]['C_Zi']) +
                        len(teacher_interval[s[3]]['C_Interval'])
                         ) for s in list_neigh]
            index =  np.random.choice(len(list_neigh), p=softmax(-np.array(scores)))
            tuplu = list_neigh[index]
            state = tuplu[0]
        if state.check_final_state_course(course):
            reward = 1
            reward -= float(optional(state.orar,dict_file))/20
        else:
            reward = 0
        new_new_node = node
        while new_new_node:
            new_new_node[N] += 1
            new_new_node[Q] +=  reward
            new_new_node = new_new_node[PARENT]
    if tree:
        final_action = select_action(tree, 0.0)
        return (final_action, tree[ACTIONS][final_action],states)
                  
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Not enough arguments")
        sys.exit(1)
    method = sys.argv[1]
    file = sys.argv[2]
    path = "inputs/" + file
    dict_file = read_yaml_file(path)
    timetable_struc = {}
    for zi in dict_file['Zile']:
        timetable_struc[zi] = {}
        for ora in dict_file['Intervale']:
            ora_tup  = eval(ora)
            timetable_struc[zi][ora_tup] = {}
            for sala in dict_file['Sali']:
                timetable_struc[zi][ora_tup][sala] = None
    courses = {materie: {} for materie in dict_file['Materii']}
    courses_rooms = {materie: [] for materie in dict_file['Materii']}
    days_restriction = {day: 0 for day in dict_file['Zile']}
    timetabel_teacher = {teacher:{} for teacher in dict_file['Profesori']}
    teacher_interval = {teacher:{"C_Zi":[],"C_Interval":[]} for teacher in dict_file['Profesori']}

    for room in dict_file['Sali']:
        for course in dict_file['Sali'][room]['Materii']:
            courses_rooms[course].append(room)
    for profesor, data_profesor in dict_file['Profesori'].items():
        for elem in data_profesor['Constrangeri']:
            if "-" not in elem and "!" not in elem:
                days_restriction[elem] += 1
        for materie in data_profesor['Materii']:
            courses[materie][profesor] = {'Interval': [], 'Zi': []} 
            for elem in data_profesor['Constrangeri']:
                if "-" in elem:
                    interval_list = check_interval(elem)
                    prof_interval = courses[materie][profesor]['Interval']
                    prof_interval.extend(
                        interval for interval in interval_list if interval not in prof_interval)
                    prof_interval_c = teacher_interval[profesor]["C_Interval"]
                    prof_interval_c.extend(
                        interval for interval in interval_list if interval not in prof_interval_c and "!" not in interval)  
                elif "Pauza" in elem:
                    timetabel_teacher[profesor]["Pauza"] = int(elem.split(" ")[2])
                else:
                    courses[materie][profesor]['Zi'].append(elem)
                    prof_zi_c = teacher_interval[profesor]["C_Zi"]
                    if elem not in prof_zi_c and "!" not in elem:
                        prof_zi_c.append(elem)
    nr_students = {course: dict_file['Materii'][course] for course in dict_file['Materii']}
    euristica = sorted(dict_file['Materii'], key=lambda x: (len(courses_rooms[x]),-nr_students[x]), reverse=False)
    hours_course = dict_file['Materii']
    state_initial = State(timetable_struc,0,{teacher:0 for teacher in dict_file['Profesori']},hours_course)
    queueP = Queue(maxsize=len(euristica))
    for elem in euristica:
        queueP.put(elem)
    if method == "hc":
        start = time()
        final, state, iters, states = hill_climbing(state_initial,queueP)
        end = time()
        if os.path.isdir("outputs_hill") == False:
            os.mkdir("outputs_hill")
        with open(f"outputs_hill/{file.split('.')[0]}.txt", "w") as f:
            f.write(pretty_print_timetable(state.orar,path))
            f.write("Numar stari: " + str(states) + "\n")
            f.write("Numar iteratii: " + str(iters) + "\n")
            f.write("Mandatory constraints: " + str(mandatory(state.orar,dict_file)) + "\n")
            f.write("Optional constraints: " + str(optional(state.orar,dict_file)) + "\n")
            f.write("Time: " + str(end-start) + "\n")
            if file == "orar_bonus_exact.yaml":
                f.write("Nr pauze incalcate: " + str(state.nconflicts//10 + state.nconflicts%10 - optional(state.orar,dict_file)) + "\n")
    elif method == "mcts":
        start = time()
        state = state_initial
        last_action = None
        iters = 0
        states = 0
        while not queueP.empty():
            course = queueP.get()
            while(state.hours_course[course] > 0):
                (action, tree,recv_states) = mcts(state,5,last_action,course) 
                states += recv_states    
                iters += 5
                state = tree[STATE]
                last_action = tree
        end = time()
        if os.path.isdir("outputs_mcts") == False:
            os.mkdir("outputs_mcts")
        with open(f"outputs_mcts/{file.split('.')[0]}.txt", "w") as f:
            f.write(pretty_print_timetable(state.orar,path))
            f.write("Numar iteratii: " + str(iters) + "\n")
            f.write("Numar stari: " + str(states) + "\n")
            f.write("Mandatory constraints: " + str(mandatory(state.orar,dict_file)) + "\n")
            f.write("Optional constraints: " + str(optional(state.orar,dict_file)) + "\n")
            f.write("Time: " + str(end-start) + "\n")
            if file == "orar_bonus_exact.yaml":
                f.write("Nr pauze incalcate: " + str(state.nconflicts//10 + state.nconflicts%10 - optional(state.orar,dict_file)) + "\n")
        
