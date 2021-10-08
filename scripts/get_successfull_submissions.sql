-- replace phase_id with correct ID
SELECT * FROM submissions_submission
JOIN teams_team ON submissions_submission.team_id = teams_team.id
JOIN submissions_measurement ON submissions_submission.id = submissions_measurement.submission_id
WHERE submissions_submission.phase_id = 12 and submissions_submission.status = 70;
