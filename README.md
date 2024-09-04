# Automatic Timetable Generator
## Overview

This project implements an automatic timetable generator using Python. The generator aims to create a conflict-free (or minimally conflicted) schedule based on constraints commonly found in academic timetables. The implementation leverages both Hill-Climbing and Monte-Carlo Tree Search algorithms to optimize the timetable.
## Features

 - Time Slots: Each time slot is 120 minutes long, with 6 slots available per day (from 8:00 AM to 8:00 PM).
 - Days: The schedule is generated for a 5-day week (Monday to Friday).
 - Room Allocation: Limited number of rooms with specific capacities and subject assignments.
 - Student Distribution: Ensures all students enrolled in a subject have allocated sessions in rooms that can accommodate them.
 - Teacher Constraints: Teachers are assigned to subjects based on their specialization and have preferences for specific days and times.

## Constraints
### Hard Constraints

These constraints must be strictly followed to generate a valid timetable:

  - A room can host only one subject per time slot.
  -  A teacher can teach only one subject in a single time slot.
 - Teachers can teach a maximum of 7 slots per week.
- The number of students in a room cannot exceed the room's capacity.
- All students must have their classes scheduled for each subject they are enrolled in.
- Teachers can only teach subjects they are specialized in.
 - Rooms are allocated only for the subjects they are assigned to.

### Soft Constraints

These constraints are preferences that, if violated, should be minimized:

  - Teacher preferences for specific days (e.g., preferring to teach on Mondays, avoiding Tuesdays).
  - Teacher preferences for specific time slots (e.g., preferring to teach in the morning).
  -  Minimizing gaps in the teachers' schedules (e.g., avoiding breaks longer than a specified number of hours).

## Optimization Approach

The timetable generator uses two algorithms to optimize the schedule:
### 1. Hill-Climbing Algorithm

Hill-Climbing is a heuristic search algorithm used to find an optimal solution by iteratively improving the current solution. Starting from an initial valid timetable, the algorithm explores neighboring schedules and selects the best one, continuing this process until no further improvements can be made.
### 2. Monte-Carlo Tree Search (MCTS)

Monte-Carlo Tree Search (MCTS) is a decision-making algorithm that uses random simulations to explore possible outcomes and make optimal choices. In this project, MCTS is applied to explore different timetable configurations and select the one with the highest potential, balancing between exploration of new possibilities and exploitation of known good schedules.

## Usage

To run the timetable generator, use the orar.py script followed by the algorithm name and the input file:

```bash
python orar.py <alg> <input_file>
```
-  <input_file>: Provide the path to the input file containing the timetable data.
-  <alg>: Specify the algorithm to use, either hill_climbing or mcts.
