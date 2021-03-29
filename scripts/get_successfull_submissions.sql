-- replace phase_id with correct ID
SELECT * FROM submissions_submission JOIN teams_team ON submissions_submission.team_id = teams_team.id WHERE submissions_submission.phase_id = 11 and submissions_submission.status = 70;
