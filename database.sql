CREATE TABLE users(
  first_name VARCHAR(30),
  last_name VARCHAR(30),
  mail VARCHAR(50) PRIMARY KEY,
  password VARCHAR(15) not null,
  maso VARCHAR(10) not null unique,
  role CHAR(2) not null, 
  created_at timestamp
);

CREATE TABLE posts(
  id integer PRIMARY KEY,
  student_mail VARCHAR(50) not null REFERENCES users(mail),
  verified_teacher_mail VARCHAR(50) REFERENCES users(mail),
  title VARCHAR(255) not null,
  description VARCHAR(1500) not null,
  title_en VARCHAR(255),
  description_en VARCHAR(1500),
  subject VARCHAR(100) not null,
  trace VARCHAR(255),
  created_at timestamp
);

CREATE TABLE tags(
  id integer PRIMARY KEY,
  name varchar(255) not null
);

CREATE TABLE post_has_tags(
  post_id integer not null REFERENCES posts(id),
  tag_id integer not null REFERENCES tags(id),
  PRIMARY KEY (post_id, tag_id)
);

CREATE TABLE teacher_verify_post(
  post_id integer not null REFERENCES posts(id),
  teacher_mail VARCHAR(50) not null REFERENCES users(mail),
  PRIMARY KEY (post_id)
);

CREATE TABLE interactions(  
  id integer not null,
  user_mail VARCHAR(50) not null REFERENCES users(mail),
  post_id integer not null REFERENCES posts(id),
  created_at timestamp,
  type varchar(10),
  rating integer,
  isLike boolean,
  PRIMARY KEY (id, post_id)
);

CREATE TABLE comments(
  id integer not null,
  user_mail VARCHAR(50) not null REFERENCES users(mail),
  post_id integer not null REFERENCES posts(id),
  content varchar(300),
  parentID integer,
  created_at timestamp,
  PRIMARY KEY (id, post_id)
);

CREATE TABLE user_like_comment(
  user_mail VARCHAR(50) not null REFERENCES users(mail), 
  comment_id integer not null,
  post_id integer not null,
  PRIMARY KEY (comment_id, post_id),
  FOREIGN KEY (comment_id, post_id) REFERENCES comments(id, post_id)
);

CREATE TABLE testcases(
  post_id integer not null REFERENCES posts(id),
  input varchar(100) not null,
  expected varchar(100) not null,
  PRIMARY KEY (post_id)
);

CREATE TABLE student_run_testcases(
  ID integer PRIMARY KEY,
  post_id integer not null REFERENCES testcases(post_id),
  student_mail varchar(50) not null REFERENCES users(mail), 
  log varchar(50),
  score integer,
  time timestamp
);

CREATE INDEX idx_studentRunTestcase_student_mail_time
ON studentRunTestcase (student_mail, time DESC);

CREATE INDEX idx_posts_subject_trace
ON posts (subject, trace);

CREATE INDEX idx_posts_created_at
ON posts (created_at DESC);

CREATE INDEX idx_interactions_post_id
ON interactions (post_id);

CREATE INDEX idx_comments_post_id
ON comments (post_id);

INSERT INTO users (first_name, last_name, mail, password, maso, role, created_at) VALUES
('Dang', 'Hoang', 'dang.hoang1205@hcmut.edu.vn', '123456', '2110120', 'SV', NOW()),
('Son', 'Nguyen', 'son.nguyenthai@hcmut.edu.vn', '123456', '2112198', 'SV', NOW()),
('A', 'Nguyen', 'a.nguyen@hcmut.edu.vn', '123456', '2110001', 'SV', NOW()),
('B', 'Nguyen', 'b.nguyen@hcmut.edu.vn', '123456', '2110002', 'SV', NOW()),
('C', 'Nguyen', 'c.nguyen@hcmut.edu.vn', '123456', '2110003', 'SV', NOW()),
('D', 'Nguyen', 'd.nguyen@hcmut.edu.vn', '123456', '2110004', 'SV', NOW()),
('E', 'Nguyen', 'e.nguyen@hcmut.edu.vn', '123456', '2110005', 'SV', NOW());

INSERT INTO posts (id, student_mail, verified_teacher_mail, title, description, subject, trace, created_at) VALUES
(1, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Test Cases for Stack Operations', 'This post provides detailed test cases for stack operations to ensure correctness and efficiency. The test cases cover basic operations (Push, Pop, Top): Verify functionality for both empty and non-empty stacks, and edge cases like stack overflow.', 'DSA', 'Data Structures and Algorithms > Chap 5: Stack and Queue > Basic operations of Stacks', NOW()),
(2, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Test Cases for Quick Sort Algorithms', 'This post provides detailed test cases for Quick Sort algorithm to ensure correctness and efficiency.', 'DSA', 'Data Structures and Algorithms > Chap 3: Recursion > Basic components of recursive algorithms', NOW()),
(3, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Stack Implementation and Use Cases', 'This post explains stack data structure implementation and its applications in function calls, expression evaluation, and backtracking.', 'DSA', 'Data Structures and Algorithms > Chap 5: Stack and Queue > Stack', NOW()),
(4, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Queue vs Deque: Differences and Applications', 'An in-depth comparison between Queue and Deque, discussing their differences, time complexity, and practical applications in scheduling.', 'DSA', 'Data Structures and Algorithms > Chap 6: Trees > Binary Trees', NOW()),
(5, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Singly Linked List: Insertion and Deletion', 'This post covers how to implement insertion and deletion operations in a singly linked list with C++ and Python examples.', 'DSA', 'Data Structures and Algorithms > Chap 9: Sorting > Straight Insertion Sort', NOW()),
(6, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Doubly Linked List: Advantages and Implementation', 'Explains the benefits of using a doubly linked list over a singly linked list and demonstrates basic operations.', 'DSA', 'Data Structures and Algorithms > Chap 9: Sorting > Straight Insertion Sort', NOW()),
(7, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Binary Search Tree (BST) Operations', 'A comprehensive guide on BST including insertion, deletion, search, and traversal techniques (Inorder, Preorder, Postorder).', 'DSA', 'Data Structures and Algorithms > Chap 6: Trees > Application of Trees', NOW()),
(8, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Heap Data Structure and Priority Queues', 'Discusses heap implementation and its importance in priority queues, along with applications in scheduling algorithms.', 'DSA', 'Data Structures and Algorithms > Chap 9: Sorting > Exchange Sort', NOW()),
(9, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Hash Tables and Collision Resolution Techniques', 'Explains hash tables, hashing functions, and various collision resolution methods such as chaining and open addressing.', 'DSA', 'Data Structures and Algorithms > Chap 3: Recursion > Backtracking', NOW()),
(10, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Bubble Sort: Algorithm and Time Complexity', 'An in-depth analysis of the Bubble Sort algorithm, including its working principle and worst-case time complexity.', 'DSA', 'Data Structures and Algorithms > Chap 9: Sorting > Straight Selection Sort', NOW()),
(11, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Selection Sort: When to Use It?', 'Describes how Selection Sort works and compares its efficiency with other sorting algorithms like Merge Sort and Quick Sort.', 'DSA', 'Data Structures and Algorithms > Chap 9: Sorting > Straight Selection Sort', NOW()),
(12, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Insertion Sort: Best Cases and Real-World Uses', 'Covers the working of Insertion Sort, why it is useful for nearly sorted data, and where it is applied in real-world scenarios.', 'DSA', 'Data Structures and Algorithms > Chap 1: Introduction > Algorithm', NOW()),
(13, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Merge Sort: Divide and Conquer Approach', 'Explains the divide-and-conquer strategy used in Merge Sort and its advantages over other sorting techniques.', 'DSA', 'Data Structures and Algorithms > Chap 9: Sorting > Merge Sort', NOW()),
(14, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Quick Sort: Efficient Partitioning Strategy', 'Covers the Quick Sort algorithm with Lomuto and Hoare partition schemes, and compares its performance with Merge Sort.', 'DSA', 'Data Structures and Algorithms > Chap 9: Sorting > Merge Sort', NOW()),
(15, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Heap Sort: Sorting with Heaps', 'A detailed explanation of Heap Sort, how it leverages the heap structure for efficient sorting, and its practical applications.', 'DSA', 'Data Structures and Algorithms > Chap 8: Heaps > Heap Applications', NOW()),
(16, 'dang.hoang1205@hcmut.edu.vn', NULL, 'Testcase for Insertion in a General Unordered List', 'Testcase to verify the insertion of an element at a specified position in a general unordered list.', 'DSA', 'Data Structures and Algorithms > Chap 6: Trees > Application of Trees', NOW()),
(17, 'a.nguyen@hcmut.edu.vn', NULL, 'Testcase for Insertion in a General Ordered List', 'Testcase to verify the insertion of an element in a general ordered list while maintaining the order.', 'DSA', 'Data Structures and Algorithms > Chap 6: Trees > Application of Trees', NOW()),
(18, 'a.nguyen@hcmut.edu.vn', NULL, 'Testcase for Removal in a General Unordered List', 'Testcase to verify the removal of an element at a specified position in a general unordered list.', 'DSA', 'Data Structures and Algorithms > Chap 4: List > Retrieval', NOW()),
(19, 'd.nguyen@hcmut.edu.vn', NULL, 'Testcase for Removal in a General Ordered List', 'Testcase to verify the removal of an element at a specified position in a general ordered list.', 'DSA', 'Data Structures and Algorithms > Chap 4: List > Success of Basic Operations', NOW()),
(20, 'b.nguyen@hcmut.edu.vn', NULL, 'Testcase for Insertion in a Linked List', 'Testcase to verify the insertion of a node into a linked list.', 'DSA', 'Data Structures and Algorithms > Chap 9: Sorting > Straight Insertion Sort', NOW()),
(21, 'a.nguyen@hcmut.edu.vn', NULL, 'Testcase for Deletion in a Linked List', 'Testcase to verify the deletion of a node from a linked list.', 'DSA', 'Data Structures and Algorithms > Chap 9: Sorting > Straight Insertion Sort', NOW()),
(22, 'b.nguyen@hcmut.edu.vn', NULL, 'Testcase for Searching in a Linked List', 'Testcase to verify the search operation in a linked list.', 'DSA', 'Data Structures and Algorithms > Chap 4: List > Success of Basic Operations', NOW()),
(23, 'c.nguyen@hcmut.edu.vn', NULL, 'Testcase for Traversal in a Linked List', 'Testcase to verify the traversal of a linked list.', 'DSA', 'Data Structures and Algorithms > Chap 9: Sorting > Straight Insertion Sort', NOW());

INSERT INTO testcases (post_id, input, expected) VALUES
(1, 123, 'successfull'),
(2, 123, 'successfull'),
(3, 123, 'successfull'),
(4, 123, 'successfull'),
(5, 123, 'successfull'),
(6, 123, 'successfull'),
(7, 123, 'successfull'),
(8, 123, 'successfull'),
(9, 123, 'successfull'),
(10, 123, 'successfull'),
(11, 123, 'successfull'),
(12, 123, 'successfull'),
(13, 123, 'successfull'),
(14, 123, 'successfull'),
(15, 123, 'successfull'),
(16, 123, 'successfull'),
(17, 123, 'successfull'),
(18, 123, 'successfull'),
(19, 123, 'successfull'),
(20, 123, 'successfull'),
(21, 123, 'successfull'),
(22, 123, 'successfull'),
(23, 123, 'successfull');

INSERT INTO student_run_testcases (id, post_id, student_mail, log, score, time) VALUES
(1, 11, 'son.nguyenthai@hcmut.edu.vn', null, 1, NOW()),
(2, 12, 'son.nguyenthai@hcmut.edu.vn', null, 0, NOW()),
(3, 13, 'son.nguyenthai@hcmut.edu.vn', null, 1, NOW()),
(4, 14, 'son.nguyenthai@hcmut.edu.vn', null, 1, NOW());

INSERT INTO interactions (id, user_mail, post_id, created_at, type, rating, islike) VALUES
(1, 'dang.hoang1205@hcmut.edu.vn', 5, NOW(), 'rating', 4.0, NULL),
(2, 'dang.hoang1205@hcmut.edu.vn', 5, NOW(), 'rating', 5.0, NULL),
(3, 'a.nguyen@hcmut.edu.vn', 6, NOW(), 'like', NULL, True),
(4, 'b.nguyen@hcmut.edu.vn', 11, NOW(), 'rating', 4.0, NULL),
(5, 'c.nguyen@hcmut.edu.vn', 12, NOW(), 'like', NULL, True),
(6, 'd.nguyen@hcmut.edu.vn', 13, NOW(), 'rating', 3.0, NULL),
(7, 'son.nguyenthai@hcmut.edu.vn', 14, NOW(), 'like', NULL, True),
(8, 'dang.hoang1205@hcmut.edu.vn', 20, NOW(), 'rating', 5.0, NULL),
(9, 'a.nguyen@hcmut.edu.vn', 21, NOW(), 'like', NULL, True),
(10, 'b.nguyen@hcmut.edu.vn', 23, NOW(), 'rating', 4.0, NULL),
(11, 'c.nguyen@hcmut.edu.vn', 5, NOW(), 'like', NULL, True),
(12, 'd.nguyen@hcmut.edu.vn', 6, NOW(), 'rating', 2.0, NULL),
(13, 'son.nguyenthai@hcmut.edu.vn', 11, NOW(), 'like', NULL, True),
(14, 'dang.hoang1205@hcmut.edu.vn', 12, NOW(), 'rating', 3.0, NULL),
(15, 'a.nguyen@hcmut.edu.vn', 13, NOW(), 'like', NULL, True),
(16, 'b.nguyen@hcmut.edu.vn', 14, NOW(), 'rating', 5.0, NULL),
(17, 'c.nguyen@hcmut.edu.vn', 20, NOW(), 'like', NULL, True),
(18, 'd.nguyen@hcmut.edu.vn', 21, NOW(), 'rating', 4.0, NULL),
(19, 'son.nguyenthai@hcmut.edu.vn', 23, NOW(), 'like', NULL, True),
(20, 'dang.hoang1205@hcmut.edu.vn', 5, NOW(), 'rating', 3.0, NULL),
(21, 'a.nguyen@hcmut.edu.vn', 6, NOW(), 'like', NULL, True);

INSERT INTO comments (id, user_mail, post_id, content, parentid, created_at) VALUES
(1, 'dang.hoang1205@hcmut.edu.vn', 5, 'Bổ ích', NULL, NOW()),
(2, 'a.nguyen@hcmut.edu.vn', 6, 'Rất hay, cảm ơn bạn!', NULL, NOW()),
(3, 'b.nguyen@hcmut.edu.vn', 11, 'Mình chưa hiểu lắm, có thể giải thích thêm không?', NULL, NOW()),
(4, 'c.nguyen@hcmut.edu.vn', 12, 'Cảm ơn bạn đã chia sẻ!', NULL, NOW()),
(5, 'd.nguyen@hcmut.edu.vn', 13, 'Bài viết rất chi tiết!', NULL, NOW()),
(6, 'son.nguyenthai@hcmut.edu.vn', 14, 'Có thể bổ sung thêm ví dụ không?', NULL, NOW()),
(7, 'dang.hoang1205@hcmut.edu.vn', 20, 'Tuyệt vời!', NULL, NOW()),
(8, 'a.nguyen@hcmut.edu.vn', 21, 'Bài viết hữu ích cho mình!', NULL, NOW()),
(9, 'b.nguyen@hcmut.edu.vn', 23, 'Cảm ơn bạn, mình đã hiểu hơn!', NULL, NOW()),
(10, 'c.nguyen@hcmut.edu.vn', 5, 'Mình nghĩ nên bổ sung thêm hình ảnh.', NULL, NOW()),
(11, 'd.nguyen@hcmut.edu.vn', 6, 'Có ai áp dụng được chưa?', NULL, NOW()),
(12, 'son.nguyenthai@hcmut.edu.vn', 11, 'Rất thực tế, cảm ơn bạn!', NULL, NOW()),
(13, 'dang.hoang1205@hcmut.edu.vn', 12, 'Mình thấy phần này hơi khó hiểu!', NULL, NOW()),
(14, 'a.nguyen@hcmut.edu.vn', 13, 'Bạn có thể chia sẻ thêm tài liệu tham khảo không?', NULL, NOW()),
(15, 'b.nguyen@hcmut.edu.vn', 14, 'Rất chi tiết, mình sẽ thử áp dụng.', NULL, NOW()),
(16, 'c.nguyen@hcmut.edu.vn', 20, 'Có thể giải thích rõ hơn về bước 3 không?', NULL, NOW()),
(17, 'd.nguyen@hcmut.edu.vn', 21, 'Bài viết rất sát với thực tế!', NULL, NOW()),
(18, 'son.nguyenthai@hcmut.edu.vn', 23, 'Mình đã thử và thấy rất hữu ích!', NULL, NOW()),
(19, 'dang.hoang1205@hcmut.edu.vn', 5, 'Cảm ơn bạn, mình đã hiểu hơn về chủ đề này.', NULL, NOW()),
(20, 'a.nguyen@hcmut.edu.vn', 6, 'Bạn có thể làm thêm video hướng dẫn không?', NULL, NOW());