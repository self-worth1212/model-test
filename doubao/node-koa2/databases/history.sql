-- 创建浏览历史表
CREATE TABLE IF NOT EXISTS `history` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键id',
  `userId` int(11) NOT NULL COMMENT '用户 id',
  `todoId` int(11) NOT NULL COMMENT '待办事项 id',
  `browseTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '浏览时间',
  `createdAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updatedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `userId_todoId` (`userId`, `todoId`),
  KEY `userId` (`userId`),
  KEY `todoId` (`todoId`),
  KEY `browseTime` (`browseTime`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='浏览历史表';