INSERT INTO users (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO items (creator_id, name)
VALUES
	(2, 'item name 1'),
	(2, 'item name 2'),
	(2, 'item name 3'),
	(3, 'item name 4');

INSERT INTO details (creator_id, name, description)
VALUES
	(2, 'detail name 1', 'detail description 1'),
	(2, 'detail name 2', 'detail description 2'),
	(2, 'detail name 3', 'detail description 3'),
	(3, 'detail name 4', 'detail description 4');

INSERT INTO item_detail_relations (item_id, detail_id, content)
VALUES
	(1, 1, 'relation content 1'),
	(2, 1, 'relation content 2'),
	(3, 2, 'relation content 3');

INSERT INTO lists (creator_id, name, description)
VALUES
	(2, 'list name 1', 'list description 1'),
	(2, 'list name 2', 'list description 2'),
	(3, 'list name 3', 'list description 3'),
	(3, 'list name 4', 'list description 4');

INSERT INTO list_item_relations (list_id, item_id)
VALUES
	(1, 1),
	(1, 2),
	(2, 3),
	(3, 4),
	(3, 5),
	(5, 6);

INSERT INTO list_detail_relations (list_id, detail_id)
VALUES
	(1, 1),
	(1, 2),
	(2, 3),
	(3, 4),
	(3, 5),
	(4, 6);
