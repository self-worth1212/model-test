const Router = require("koa-router");
const router = new Router({ prefix: "/history" });
const { addHistory, getHistoryList } = require("@controller/history");
const { authVerify } = require("@middlewares/authVerify");

// 记录浏览历史
router.post("/add", authVerify, addHistory);

// 获取浏览历史列表
router.get("/list", authVerify, getHistoryList);

module.exports = router;