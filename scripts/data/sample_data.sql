-- 샘플 데이터 생성 (scripts/data/sample_data.sql)

-- 사용자 (password_hash NOT NULL 제약 충족, 명시적 ID 사용)
INSERT INTO users (id, email, username, password_hash, phone, status, created_at)
VALUES
(1, 'john.doe@email.com', 'johndoe', '$2y$10$abcdefghijklmnopqrstuvabcdefghijklmnopqrstuvabcdef', '010-1234-5678', 'active', NOW() - INTERVAL '60 days'),
(2, 'jane.smith@email.com', 'janesmith', '$2y$10$abcdefghijklmnopqrstuvabcdefghijklmnopqrstuvabcdef', '010-2345-6789', 'active', NOW() - INTERVAL '55 days'),
(3, 'minsu.kim@email.com', 'minkim', '$2y$10$abcdefghijklmnopqrstuvabcdefghijklmnopqrstuvabcdef', '010-3456-7890', 'active', NOW() - INTERVAL '50 days'),
(4, 'sujin.lee@email.com', 'sujinlee', '$2y$10$abcdefghijklmnopqrstuvabcdefghijklmnopqrstuvabcdef', '010-4567-8901', 'active', NOW() - INTERVAL '45 days'),
(5, 'yuna.park@email.com', 'yunapark', '$2y$10$abcdefghijklmnopqrstuvabcdefghijklmnopqrstuvabcdef', '010-5678-9012', 'active', NOW() - INTERVAL '40 days'),
(6, 'hyunwoo.choi@email.com', 'hchoi', '$2y$10$abcdefghijklmnopqrstuvabcdefghijklmnopqrstuvabcdef', '010-6789-0123', 'inactive', NOW() - INTERVAL '35 days'),
(7, 'ara.kim@email.com', 'arakim', '$2y$10$abcdefghijklmnopqrstuvabcdefghijklmnopqrstuvabcdef', '010-7890-1234', 'active', NOW() - INTERVAL '30 days'),
(8, 'daehyun.oh@email.com', 'doh', '$2y$10$abcdefghijklmnopqrstuvabcdefghijklmnopqrstuvabcdef', '010-8901-2345', 'suspended', NOW() - INTERVAL '25 days'),
(9, 'eunji.han@email.com', 'ejhan', '$2y$10$abcdefghijklmnopqrstuvabcdefghijklmnopqrstuvabcdef', '010-9012-3456', 'active', NOW() - INTERVAL '20 days'),
(10, 'taeyang.park@email.com', 'typark', '$2y$10$abcdefghijklmnopqrstuvabcdefghijklmnopqrstuvabcdef', '010-0123-4567', 'active', NOW() - INTERVAL '15 days');

-- 배송 주소 (기본 주소 포함, 명시적 ID 사용)
INSERT INTO user_addresses (id, user_id, name, phone, address, detail_address, postal_code, city, state, is_default)
VALUES
(1, 1, 'John Doe', '010-1234-5678', '서울시 강남구 테헤란로 123', '101동 1001호', '06236', '서울', '서울', TRUE),
(2, 1, 'John Doe(회사)', '010-1234-5678', '서울시 송파구 송파대로 55', 'A동 3층', '05718', '서울', '서울', FALSE),
(3, 2, 'Jane Smith', '010-2345-6789', '부산시 해운대구 센텀서로 45', '502호', '48059', '부산', '부산', TRUE),
(4, 3, '김민수', '010-3456-7890', '인천시 연수구 송도과학로 32', 'B동 802호', '21984', '인천', '인천', TRUE),
(5, 4, '이수진', '010-4567-8901', '대전시 유성구 대학로 99', '1203호', '34134', '대전', '대전', TRUE),
(6, 5, '박유나', '010-5678-9012', '광주시 북구 비엔날레로 20', '2층', '61048', '광주', '광주', TRUE),
(7, 6, '최현우', '010-6789-0123', '대구시 수성구 달구벌대로 100', '701호', '42029', '대구', '대구', TRUE),
(8, 7, '김아라', '010-7890-1234', '울산시 남구 삼산로 10', '305호', '44684', '울산', '울산', TRUE),
(9, 8, '오대현', '010-8901-2345', '세종시 나성북1로 11', '201호', '30147', '세종', '세종', TRUE),
(10, 9, '한은지', '010-9012-3456', '경기도 성남시 분당구 판교역로 150', '808호', '13494', '성남', '경기', TRUE),
(11, 10, '박태양', '010-0123-4567', '경기도 고양시 일산서구 중앙로 25', '1204호', '10369', '고양', '경기', TRUE),
(12, 2, 'Jane Smith(부모님)', '010-2345-6789', '부산시 수영구 남천동 12', '별관 2층', '48270', '부산', '부산', FALSE);

-- 카테고리 (계층 포함)
INSERT INTO categories (id, name, parent_id, description, display_order, is_active)
VALUES
(1, 'Electronics', NULL, '전자기기', 1, TRUE),
(2, 'Home & Kitchen', NULL, '가전 및 주방', 2, TRUE),
(3, 'Fashion', NULL, '의류/잡화', 3, TRUE),
(4, 'Mobile Phones', 1, '스마트폰', 1, TRUE),
(5, 'Laptops', 1, '노트북', 2, TRUE),
(6, 'Accessories', 1, '악세서리', 3, TRUE),
(7, 'Appliances', 2, '생활가전', 1, TRUE),
(8, 'Furniture', 2, '가구', 2, TRUE),
(9, 'Men', 3, '남성의류', 1, TRUE),
(10, 'Women', 3, '여성의류', 2, TRUE);

-- 상품
INSERT INTO products (id, category_id, name, description, price, cost, brand, model, status, weight, dimensions, created_at)
VALUES
(1, 4, 'iPhone 15', 'Apple 스마트폰', 1500000.00, 1200000.00, 'Apple', 'iPhone 15', 'active', 0.20, '147x71x7.8mm', NOW() - INTERVAL '40 days'),
(2, 4, 'Galaxy S24', 'Samsung 스마트폰', 1390000.00, 1100000.00, 'Samsung', 'SM-S921', 'active', 0.21, '146x70x7.6mm', NOW() - INTERVAL '39 days'),
(3, 5, 'MacBook Air M2', '13-inch, 8GB/256GB', 1800000.00, 1500000.00, 'Apple', 'A2681', 'active', 1.24, '304x215x11.3mm', NOW() - INTERVAL '38 days'),
(4, 5, 'Dell XPS 13', '13-inch, 16GB/512GB', 1750000.00, 1450000.00, 'Dell', 'XPS 9315', 'active', 1.20, '295x199x14.8mm', NOW() - INTERVAL '37 days'),
(5, 6, 'USB-C Cable 1m', '고속충전/데이터', 15000.00, 5000.00, 'Anker', 'A81B1', 'active', 0.05, '1000mm', NOW() - INTERVAL '36 days'),
(6, 6, 'Wireless Charger', '15W 무선충전패드', 45000.00, 20000.00, 'Belkin', 'WCP001', 'active', 0.10, '90x90x8mm', NOW() - INTERVAL '35 days'),
(7, 7, 'Air Fryer 5L', '대용량 에어프라이어', 129000.00, 90000.00, 'Philips', 'HD9252', 'active', 4.50, '360x295x330mm', NOW() - INTERVAL '34 days'),
(8, 7, 'Vacuum Cleaner', '무선 청소기', 199000.00, 140000.00, 'LG', 'A9', 'active', 3.00, '260x210x1120mm', NOW() - INTERVAL '33 days'),
(9, 8, 'Dining Table', '6인용 식탁', 320000.00, 220000.00, 'IKEA', 'LACK-D', 'active', 30.00, '1800x900x750mm', NOW() - INTERVAL '32 days'),
(10, 8, 'Office Chair', '메쉬 백 오피스 체어', 150000.00, 90000.00, 'HermanMiller', 'HM-OC', 'active', 12.00, '650x650x1200mm', NOW() - INTERVAL '31 days'),
(11, 9, 'Men''s Jacket', '봄/가을용 재킷', 99000.00, 50000.00, 'Uniqlo', 'UJ-2025', 'active', 0.80, 'M', NOW() - INTERVAL '30 days'),
(12, 10, 'Women''s Sneakers', '경량 스니커즈', 89000.00, 45000.00, 'Nike', 'NK-WS', 'active', 0.65, '240mm', NOW() - INTERVAL '29 days');

-- 재고
INSERT INTO inventory (id, product_id, quantity, reserved_quantity, reorder_level, warehouse_location, last_updated)
VALUES
(1, 1, 50, 5, 10, 'WH-A-01', NOW() - INTERVAL '2 days'),
(2, 2, 60, 8, 10, 'WH-A-02', NOW() - INTERVAL '2 days'),
(3, 3, 25, 2, 5, 'WH-B-01', NOW() - INTERVAL '2 days'),
(4, 4, 20, 1, 5, 'WH-B-02', NOW() - INTERVAL '2 days'),
(5, 5, 500, 30, 100, 'WH-C-01', NOW() - INTERVAL '1 day'),
(6, 6, 200, 20, 50, 'WH-C-02', NOW() - INTERVAL '1 day'),
(7, 7, 80, 10, 20, 'WH-D-01', NOW() - INTERVAL '3 days'),
(8, 8, 70, 12, 20, 'WH-D-02', NOW() - INTERVAL '3 days'),
(9, 9, 15, 3, 5, 'WH-E-01', NOW() - INTERVAL '5 days'),
(10, 10, 40, 5, 10, 'WH-E-02', NOW() - INTERVAL '4 days'),
(11, 11, 120, 15, 30, 'WH-F-01', NOW() - INTERVAL '2 days'),
(12, 12, 110, 12, 30, 'WH-F-02', NOW() - INTERVAL '2 days');

-- 주문 (금액 = 아이템 합계 + 배송 + 세금 - 할인)
INSERT INTO orders (id, user_id, order_number, status, total_amount, discount_amount, shipping_fee, tax_amount, payment_method, shipping_address_id, order_date, shipped_at, delivered_at, notes)
VALUES
(1, 1, 'ORD-2025-001', 'delivered', 1518000.00, 0.00, 3000.00, 15000.00, 'card', 1, NOW() - INTERVAL '20 days', NOW() - INTERVAL '19 days', NOW() - INTERVAL '17 days', '신속 배송'),
(2, 2, 'ORD-2025-002', 'processing', 1446000.00, 5000.00, 3000.00, 13000.00, 'mobile_pay', 3, NOW() - INTERVAL '15 days', NULL, NULL, NULL),
(3, 3, 'ORD-2025-003', 'shipped', 1887000.00, 10000.00, 3000.00, 19000.00, 'card', 4, NOW() - INTERVAL '12 days', NOW() - INTERVAL '10 days', NULL, NULL),
(4, 4, 'ORD-2025-004', 'pending', 94000.00, 10000.00, 3000.00, 2000.00, 'bank_transfer', 5, NOW() - INTERVAL '9 days', NULL, NULL, '입금 대기'),
(5, 5, 'ORD-2025-005', 'cancelled', 45000.00, 0.00, 0.00, 0.00, 'card', 6, NOW() - INTERVAL '8 days', NULL, NULL, '고객 취소'),
(6, 6, 'ORD-2025-006', 'delivered', 1911000.00, 0.00, 3000.00, 19000.00, 'card', 7, NOW() - INTERVAL '25 days', NOW() - INTERVAL '24 days', NOW() - INTERVAL '22 days', NULL),
(7, 7, 'ORD-2025-007', 'delivered', 182000.00, 2000.00, 3000.00, 7000.00, 'mobile_pay', 8, NOW() - INTERVAL '6 days', NOW() - INTERVAL '5 days', NOW() - INTERVAL '3 days', NULL),
(8, 8, 'ORD-2025-008', 'refunded', 1390000.00, 0.00, 0.00, 0.00, 'card', 9, NOW() - INTERVAL '28 days', NOW() - INTERVAL '27 days', NOW() - INTERVAL '25 days', '품질 문제 환불 완료'),
(9, 9, 'ORD-2025-009', 'confirmed', 1780000.00, 20000.00, 3000.00, 17000.00, 'bank_transfer', 10, NOW() - INTERVAL '5 days', NULL, NULL, NULL),
(10, 10, 'ORD-2025-010', 'shipped', 190000.00, 0.00, 3000.00, 7000.00, 'points', 11, NOW() - INTERVAL '4 days', NOW() - INTERVAL '2 days', NULL, NULL),
(11, 2, 'ORD-2025-011', 'delivered', 276000.00, 10000.00, 3000.00, 9000.00, 'card', 12, NOW() - INTERVAL '18 days', NOW() - INTERVAL '17 days', NOW() - INTERVAL '15 days', '프로모션 적용'),
(12, 3, 'ORD-2025-012', 'processing', 1422000.00, 0.00, 3000.00, 14000.00, 'mobile_pay', 4, NOW() - INTERVAL '3 days', NULL, NULL, NULL);

-- 주문 상품 (unit_price * quantity = total_price)
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price, total_price, created_at)
VALUES
(1, 1, 1, 1, 1500000.00, 1500000.00, NOW() - INTERVAL '20 days'),
(2, 2, 2, 1, 1390000.00, 1390000.00, NOW() - INTERVAL '15 days'),
(3, 2, 5, 3, 15000.00, 45000.00, NOW() - INTERVAL '15 days'),
(4, 3, 3, 1, 1800000.00, 1800000.00, NOW() - INTERVAL '12 days'),
(5, 3, 6, 1, 45000.00, 45000.00, NOW() - INTERVAL '12 days'),
(6, 3, 5, 2, 15000.00, 30000.00, NOW() - INTERVAL '12 days'),
(7, 4, 11, 1, 99000.00, 99000.00, NOW() - INTERVAL '9 days'),
(8, 5, 6, 1, 45000.00, 45000.00, NOW() - INTERVAL '8 days'),
(9, 6, 3, 1, 1800000.00, 1800000.00, NOW() - INTERVAL '25 days'),
(10, 6, 12, 1, 89000.00, 89000.00, NOW() - INTERVAL '25 days'),
(11, 7, 7, 1, 129000.00, 129000.00, NOW() - INTERVAL '6 days'),
(12, 7, 6, 1, 45000.00, 45000.00, NOW() - INTERVAL '6 days'),
(13, 8, 2, 1, 1390000.00, 1390000.00, NOW() - INTERVAL '28 days'),
(14, 9, 4, 1, 1750000.00, 1750000.00, NOW() - INTERVAL '5 days'),
(15, 9, 5, 2, 15000.00, 30000.00, NOW() - INTERVAL '5 days'),
(16, 10, 10, 1, 150000.00, 150000.00, NOW() - INTERVAL '4 days'),
(17, 10, 5, 2, 15000.00, 30000.00, NOW() - INTERVAL '4 days'),
(18, 11, 8, 1, 199000.00, 199000.00, NOW() - INTERVAL '18 days'),
(19, 11, 6, 1, 45000.00, 45000.00, NOW() - INTERVAL '18 days'),
(20, 11, 5, 2, 15000.00, 30000.00, NOW() - INTERVAL '18 days'),
(21, 12, 2, 1, 1390000.00, 1390000.00, NOW() - INTERVAL '3 days'),
(22, 12, 5, 1, 15000.00, 15000.00, NOW() - INTERVAL '3 days');

-- 결제 (주문 총액과 일치)
INSERT INTO payments (id, order_id, payment_method, amount, status, transaction_id, gateway, paid_at, created_at)
VALUES
(1, 1, 'card', 1518000.00, 'completed', 'TID-001', 'kcp', NOW() - INTERVAL '20 days', NOW() - INTERVAL '20 days'),
(2, 2, 'mobile_pay', 1446000.00, 'pending', NULL, 'kakao', NULL, NOW() - INTERVAL '15 days'),
(3, 3, 'card', 1887000.00, 'completed', 'TID-003', 'toss', NOW() - INTERVAL '12 days', NOW() - INTERVAL '12 days'),
(4, 4, 'bank_transfer', 94000.00, 'pending', NULL, 'bank', NULL, NOW() - INTERVAL '9 days'),
(5, 5, 'card', 45000.00, 'cancelled', 'TID-005', 'kcp', NOW() - INTERVAL '8 days', NOW() - INTERVAL '8 days'),
(6, 6, 'card', 1911000.00, 'completed', 'TID-006', 'toss', NOW() - INTERVAL '25 days', NOW() - INTERVAL '25 days'),
(7, 7, 'mobile_pay', 182000.00, 'completed', 'TID-007', 'naver', NOW() - INTERVAL '6 days', NOW() - INTERVAL '6 days'),
(8, 8, 'card', 1390000.00, 'refunded', 'TID-008', 'kcp', NOW() - INTERVAL '28 days', NOW() - INTERVAL '28 days'),
(9, 9, 'bank_transfer', 1780000.00, 'pending', NULL, 'bank', NULL, NOW() - INTERVAL '5 days'),
(10, 10, 'points', 190000.00, 'completed', 'TID-010', 'internal', NOW() - INTERVAL '4 days', NOW() - INTERVAL '4 days'),
(11, 11, 'card', 276000.00, 'completed', 'TID-011', 'toss', NOW() - INTERVAL '18 days', NOW() - INTERVAL '18 days'),
(12, 12, 'mobile_pay', 1422000.00, 'pending', NULL, 'kakao', NULL, NOW() - INTERVAL '3 days');

-- 리뷰 (배송 완료 주문 기준 일부 검증됨)
INSERT INTO reviews (id, user_id, product_id, order_id, rating, title, content, is_verified_purchase, helpful_count, status, created_at)
VALUES
(1, 1, 1, 1, 5, '최고의 스마트폰', '성능과 배터리 모두 만족합니다.', TRUE, 12, 'approved', NOW() - INTERVAL '16 days'),
(2, 6, 3, 6, 4, '가벼워요', '휴대성이 좋아요. 가격은 조금 높네요.', TRUE, 5, 'approved', NOW() - INTERVAL '21 days'),
(3, 7, 7, 7, 5, '매우 만족', '요리 시간이 확 줄었어요.', TRUE, 3, 'approved', NOW() - INTERVAL '2 days'),
(4, 8, 2, 8, 2, '환불했습니다', '제품 결함으로 환불 처리되었습니다.', TRUE, 1, 'approved', NOW() - INTERVAL '24 days'),
(5, 2, 6, 11, 4, '충전 잘 됩니다', '디자인도 깔끔하고 좋아요.', TRUE, 2, 'approved', NOW() - INTERVAL '14 days'),
(6, 3, 12, NULL, 5, '가볍고 편해요', '사이즈가 딱 맞아요.', FALSE, 0, 'pending', NOW() - INTERVAL '1 day');

-- 사용자 활동 로그 (다양한 액션)
INSERT INTO user_activities (id, user_id, activity_type, product_id, session_id, ip_address, user_agent, created_at)
VALUES
(1, 1, 'login', NULL, 'SESS-001', '192.168.0.10', 'Mozilla/5.0', NOW() - INTERVAL '21 days'),
(2, 1, 'view_product', 1, 'SESS-001', '192.168.0.10', 'Mozilla/5.0', NOW() - INTERVAL '21 days'),
(3, 1, 'add_to_cart', 1, 'SESS-001', '192.168.0.10', 'Mozilla/5.0', NOW() - INTERVAL '20 days'),
(4, 2, 'login', NULL, 'SESS-002', '192.168.0.11', 'Mozilla/5.0', NOW() - INTERVAL '16 days'),
(5, 2, 'search', NULL, 'SESS-002', '192.168.0.11', 'Mozilla/5.0', NOW() - INTERVAL '16 days'),
(6, 2, 'view_product', 2, 'SESS-002', '192.168.0.11', 'Mozilla/5.0', NOW() - INTERVAL '15 days'),
(7, 3, 'login', NULL, 'SESS-003', '192.168.0.12', 'Mozilla/5.0', NOW() - INTERVAL '13 days'),
(8, 3, 'view_product', 3, 'SESS-003', '192.168.0.12', 'Mozilla/5.0', NOW() - INTERVAL '12 days'),
(9, 3, 'add_to_cart', 6, 'SESS-003', '192.168.0.12', 'Mozilla/5.0', NOW() - INTERVAL '12 days'),
(10, 4, 'login', NULL, 'SESS-004', '192.168.0.13', 'Mozilla/5.0', NOW() - INTERVAL '9 days'),
(11, 4, 'view_product', 11, 'SESS-004', '192.168.0.13', 'Mozilla/5.0', NOW() - INTERVAL '9 days'),
(12, 5, 'login', NULL, 'SESS-005', '192.168.0.14', 'Mozilla/5.0', NOW() - INTERVAL '8 days'),
(13, 5, 'view_product', 6, 'SESS-005', '192.168.0.14', 'Mozilla/5.0', NOW() - INTERVAL '8 days'),
(14, 6, 'login', NULL, 'SESS-006', '192.168.0.15', 'Mozilla/5.0', NOW() - INTERVAL '26 days'),
(15, 6, 'view_product', 3, 'SESS-006', '192.168.0.15', 'Mozilla/5.0', NOW() - INTERVAL '25 days'),
(16, 7, 'login', NULL, 'SESS-007', 'Mozilla/5.0', '192.168.0.16', NOW() - INTERVAL '7 days'),
(17, 7, 'add_to_cart', 7, 'SESS-007', '192.168.0.16', 'Mozilla/5.0', NOW() - INTERVAL '6 days'),
(18, 7, 'purchase', NULL, 'SESS-007', '192.168.0.16', 'Mozilla/5.0', NOW() - INTERVAL '6 days'),
(19, 8, 'login', NULL, 'SESS-008', '192.168.0.17', 'Mozilla/5.0', NOW() - INTERVAL '28 days'),
(20, 8, 'view_product', 2, 'SESS-008', '192.168.0.17', 'Mozilla/5.0', NOW() - INTERVAL '28 days'),
(21, 8, 'purchase', NULL, 'SESS-008', '192.168.0.17', 'Mozilla/5.0', NOW() - INTERVAL '28 days'),
(22, 9, 'login', NULL, 'SESS-009', '192.168.0.18', 'Mozilla/5.0', NOW() - INTERVAL '6 days'),
(23, 9, 'view_product', 4, 'SESS-009', '192.168.0.18', 'Mozilla/5.0', NOW() - INTERVAL '5 days'),
(24, 10, 'login', NULL, 'SESS-010', '192.168.0.19', 'Mozilla/5.0', NOW() - INTERVAL '4 days'),
(25, 10, 'view_product', 10, 'SESS-010', '192.168.0.19', 'Mozilla/5.0', NOW() - INTERVAL '4 days'),
(26, 10, 'add_to_cart', 5, 'SESS-010', '192.168.0.19', 'Mozilla/5.0', NOW() - INTERVAL '4 days'),
(27, 2, 'logout', NULL, 'SESS-002', '192.168.0.11', 'Mozilla/5.0', NOW() - INTERVAL '15 days'),
(28, 1, 'logout', NULL, 'SESS-001', '192.168.0.10', 'Mozilla/5.0', NOW() - INTERVAL '20 days'),
(29, 3, 'remove_from_cart', 6, 'SESS-003', '192.168.0.12', 'Mozilla/5.0', NOW() - INTERVAL '11 days'),
(30, 5, 'search', NULL, 'SESS-005', '192.168.0.14', 'Mozilla/5.0', NOW() - INTERVAL '8 days');

