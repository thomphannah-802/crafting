# crafting
## Database to track my historic and present crafting projects.

### Crafting Project Tracker

I built a personal project tracking system intended to replace several disconnected spreadsheet iterations over the last several years covering all my yarn crafting projects (specifically knitting, crochet, spinning, and weaving). To this end, I designed a relational database with a Python data layer, wrote ETL scripts to import 4 years of historical data, and capped it all off by building out a Streamlit web interface that lets me browse projects and do data entry for new and ongoing projects.

### The Initial Problem

I was using Google Sheets to house my long-running project trackers (since 2021, one file per year roughly) but found that I was missing out on a grand total function spanning years, and, more importantly as I have recently begun weaving, I was unable to build out a solution quickly in Sheets that would let me do the weaving math and also save it to the tracker, and decided to use this as a challenge to increase my Python and SQL skillset.

Ultimately this code started as the desire to build out a weaving warp calculator that would allow me to input the necessary weaving structure and project dimension decisions in order to calculate the important elements needed for a project. It lets me know how much yarn and how many ends I will need to wind given yarn of a certain size and the desired end product dimensions. Once I’ve settled on the project parameters, I can save this project into the database to reference in the future, and can update it with any lessons learned, notes, and a final project weight. 

With the weaving calculator and database situated I began to add in the parameters for tracking my other yarn-based projects. While there are a lot of similarities, at least in terms of the major long term tracking points (yardage and weight), the knitting and spinning trackers both use (and create) yarn differently than weaving. Because of this they needed to be built out separately to interact with a shared yarn stash tracker, and actually to interact with that tracker in almost opposite ways - the knitting tracker uses yarn from the yarn stash table, while the spinning tracker creates yarn to put into the yarn stash.

### What I Built 

I built out two relational SQLite databases, one for weaving and one for knitting/spinning projects with a Python data layer that communicates directly with the database. Then, to speed up data entry and allow for more intuitive interactions, I built out a Streamlit user interface, which allows me to see at a glance my current projects and yardage.

### Technologies Used

I used Python and SQLite for the codebase, with Streamlit as my user interface. I used the Pandas and openpyxl libraries to create the ETL script to upload historic data.

### Key Design Decisions

#### Two Databases:

Weaving and other yarn-based crafts, despite being seemingly similar, actually use a lot of parallel-but-different industry standards and terminology. While it is possible to convert between the two systems, for this project it seemed unnecessarily complicated to, for example, make the yarn stash list track both the standard knitting yarn weights (worsted, DK, etc) and the standard weaving yarn weights (8/4, 10/2, etc). Additionally, when knitting, yarn weight is more a suggestion than a rule, while in weaving, it is one of the core factors that influences the final project. With all this and future growth in mind, I set up two separate databases.

#### Separating Reference Data:

One of the first decisions in organizing the database was to separate reference data from project data so that the reference data could be updated without affecting historical records. Tools like looms with their own specifications, spindles, and spinning wheels are the obvious types of reference data, but I chose to make fiber preparation, spinning style, and weave structure as their own reference tables since each has limited options that I frequently select between.

#### Two-Stage Records:

To reflect the way I used my historic trackers, I built the project records to handle a “planned project” input at the beginning of the project and then, once the project is completed, a completion input. This allows the database to more accurately reflect how I work on these projects, where a single project can potentially take months or even years, with many other projects started and completed in the meantime.

#### Weaving Yarn Reference Yardage:

For weaving projects, the physical yarn weight (measured traditionally as yards-per-pound) is recorded at the time of project save, during the planning time. This means that if the yarn reference table is ever updated or changes, the historic yardage stays accurate.

#### SQLite:
Because the only person who will be using this local database is myself, I chose SQLite to keep the tool portable and with zero infrastructure.


Screenshots
