# Quality Metrics Explanation

This build uses the following quality gates and metrics:

## Quality Gates
The quality gate is configured to check these key thresholds:

- **Reliability Rating**: Must be C or better
  - A = 0 bugs
  - B = at least 1 minor bug
  - C = at least 1 major bug
  - D = at least 1 critical bug
  - E = at least 1 blocker bug

- **Security Rating**: Must be B or better
  - A = 0 vulnerabilities
  - B = at least 1 minor vulnerability
  - C = at least 1 major vulnerability 
  - D = at least 1 critical vulnerability
  - E = at least 1 blocker vulnerability

- **Maintainability Rating**: Must be C or better
  - A = <= 5% technical debt ratio
  - B = 6-10% technical debt ratio
  - C = 11-20% technical debt ratio
  - D = 21-50% technical debt ratio
  - E = > 50% technical debt ratio

## Key Metrics Monitored

- **Bugs**: Issues that represent something wrong in the code that will make the code fail.
- **Vulnerabilities**: Security issues that might be exploited by attackers.
- **Code Smells**: Maintainability issues that make the code harder to read or change.
- **Coverage**: The percentage of code covered by unit tests.
- **Duplicated Lines**: The percentage of duplicated lines in the codebase.

## Quality Gate Results

The build will be marked as unstable if the quality gate fails, meaning one or more of the 
thresholds above are not met. Check the SonarCloud dashboard for detailed results:
https://sonarcloud.io/dashboard?id=huylx222_SIT753_HD