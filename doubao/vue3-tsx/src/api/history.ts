import service from '/@/axios/service';

// 记录浏览历史
export const ApiAddHistory = (data: any) => {
  return service({
    url: '/api/history/add',
    method: 'post',
    data
  });
};

// 获取浏览历史列表
export const ApiGetHistoryList = (params: any) => {
  return service({
    url: '/api/history/list',
    method: 'get',
    params
  });
};