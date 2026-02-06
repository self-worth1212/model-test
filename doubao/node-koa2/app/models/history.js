const moment = require("moment");
const {
  Sequelize,
  Model
} = require("sequelize");

// 定义浏览历史模型
class HistoryModel extends Model {}

// 初始浏览历史模型
HistoryModel.init({
  id: {
    type: Sequelize.INTEGER,
    primaryKey: true,
    autoIncrement: true,
    comment: "主键id",
  },
  userId: {
    type: Sequelize.INTEGER,
    allowNull: false,
    comment: "用户 id"
  },
  todoId: {
    type: Sequelize.INTEGER,
    allowNull: false,
    comment: "待办事项 id"
  },
  browseTime: {
    type: Sequelize.DATE,
    allowNull: false,
    defaultValue: Sequelize.NOW,
    get() {
      return moment(this.getDataValue("browseTime")).format("YYYY-MM-DD HH:mm:ss");
    },
    comment: "浏览时间",
  },
}, {
  sequelize: require("@core/db"),
  modelName: "history",
  tableName: "history",
  indexes: [
    {
      unique: true,
      fields: ["userId", "todoId"]
    }
  ]
});

module.exports = HistoryModel;