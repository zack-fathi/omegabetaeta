INSERT INTO roles (role_name, permission_level, user_id) VALUES
('Admin', 1, (SELECT user_id FROM brothers WHERE username = 'jawadalsahlani'));
INSERT INTO roles (role_name, permission_level) VALUES
('President', 1),
('Internal Vice President', 2),
('External Vice President', 2),
('Director of Recruitment', 3),
('Director of Recruitment', 3),
('Director of Finance', 4),
('Administrator', 4),
('Director of Internal', 4),
('Director of Public Relations', 4),
('Director of Education', 4),
('Director of Philanthropy', 4),
('Director of Philanthropy', 4),
('Director of External', 4);
