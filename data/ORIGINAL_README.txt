This is a a dataset containing Integrated Development Environment (IDE) logs from an introductory programming MOOC. The dataset contains information on when actions in the IDE were performed in relation to deadlines over the different parts of the course. One exceptional aspect of the dataset is that part of the logs have been gathered at the keystroke level, allowing for fine-grained insight into the learning process. In addition to the IDE logs themselves, the dataset has information on whether students included in the data passed the course. This can facilitate further research that analyzes how time-related behavior relates to performance in introductory programming courses.

Brief explanations of the data columns of the IDE_logs.csv -file:
- student: unique identifier for each student.
- part: which of the seven parts of the course the exercise that the student is working on belongs to.
- exercise: which exercise was the action related to. The number of the exercise indicates the order of the exercises within a single part.
- eventType: which type of action happened in the IDE.
- timestamp: YYYY-MM-DD HH:MM:SS formatted timestamp.
- timeToDeadline: how many seconds before the deadline of the course part the action happened.

There are seven types of events in the IDE data:
- text_insert: text was added into the IDE (at the keystroke level).
- text_remove: text was removed from the IDE.
- text_paste: text was pasted into the IDE.
- focus_gained: the IDE gained focus (student clicked into the IDE).
- focus_lost: the IDE lost focus (student clicked away from the IDE).
- run: student executed their program.
- submit: student submitted their program.

The passed.csv -file contains two columns:
- student: unique identifier for each student (matches IDE_logs.csv).
- passed: True (student passed the course) or False (student did not pass the course).

Additional notes:
Only data from students who consented to their data being used for research and who opted in to their IDE actions being logged is included.

The data only contains metadata about the programming process. In particular, the data does not contain direct contributions from students (such as source code or information on which key was pressed).

Some students might not have many IDE logs even if they have passed the course as students could turn the IDE logging on and off at will.
