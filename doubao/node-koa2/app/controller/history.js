const moment = require("moment");
const { Op } = require("sequelize");
const HistoryModel = require("@models/history");
const TodoModel = require("@models/todo");

// 记录浏览历史
async function addHistory(ctx) {
  const { todoId } = ctx.request.body;
  const currentUser = ctx.currentUser;

  if (!todoId) {
    return ctx.error("缺少待办事项id");
  }

  // 检查待办事项是否存在
  const todo = await TodoModel.findOne({
    where: {
      id: todoId,
      userId: currentUser.userId,
      deletedAt: null,
    },
  });

  if (!todo) {
    return ctx.error("待办事项不存在");
  }

  // 检查是否已有记录，有则更新时间，无则创建
  const [history, created] = await HistoryModel.findOrCreate({
    where: {
      userId: currentUser.userId,
      todoId: todoId,
    },
    defaults: {
      browseTime: new Date(),
    },
  });

  if (!created) {
    // 更新浏览时间
    await history.update({
      browseTime: new Date(),
    });
  }

  ctx.success("记录成功");
}

// 获取浏览历史
async function getHistoryList(ctx) {
  const { page, pageSize } = ctx.query;
  const currentUser = ctx.currentUser;

  // 只查询最近一个月的记录
  const oneMonthAgo = moment().subtract(1, "month").toDate();

  const history = await HistoryModel.findAndCountAll({
    where: {
      userId: currentUser.userId,
      browseTime: {
        [Op.gte]: oneMonthAgo,
      },
    },
    order: [["browseTime", "desc"]],
    limit: Number(pageSize) || 10,
    offset: (Number(page) - 1) * (Number(pageSize) || 10) || 0,
    include: [{
      model: TodoModel,
      attributes: ["id", "title", "priority", "date"],
    }],
  });

  ctx.success("获取成功", {
    pagination: {
      page: Number(page) || 1,
      pageSize: Number(pageSize) || 10,
      total: history.count,
      totalPage: Math.ceil(history.count / (Number(pageSize) || 10)),
    },
    list: history.rows,
  });
}

module.exports = {
  addHistory,
  getHistoryList,
};