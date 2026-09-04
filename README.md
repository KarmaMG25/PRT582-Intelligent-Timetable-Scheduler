# PRT582 Intelligent Timetable Scheduler

A small Python timetable scheduler developed for the PRT582 Software Unit Testing Report.

## Constraints implemented
- Room capacity
- Lecturer availability
- Room clash prevention
- Lecturer clash prevention
- Preferred time slots with fallback
- Prerequisite ordering
- Invalid input handling
- Unschedulable-course reporting

## Run tests
```bash
python -m pytest -v
```

## Run coverage
```bash
python -m pytest --cov=scheduler --cov-report=term-missing
```

## Notes
The submitted report contains the requirements, test design, AI-assisted TDD process,
critical evaluation, testing results and reflection. Add your own GitHub repository URL
and screenshots from your local development process before submission.
