import { defineComponent, onMounted, reactive } from "vue";
import { ApiGetHistoryList } from "/@/api/history";
import EContainer from '/@/components/Container';
import EHeader from '/@/components/Header';
import EContent from '/@/components/Content';
import EAside from '/@/components/Aside';
import EFooter from '/@/components/Footer';
import styles from "./index.module.less";
import { useRouter, useRoute, RouterLink } from 'vue-router';
import { Button, Toast, List, PullRefresh } from 'vant';
import moment from 'moment';

interface HistoryState {
  currentPage: number;
  pageSize: number;
  total: number;
  historyList: any[];
  loading: boolean;
  refreshing: boolean;
}

export default defineComponent({
  name: "History",
  setup() {
    const router = useRouter();
    const route = useRoute();

    const state = reactive<HistoryState>({
      currentPage: 1,
      pageSize: 10,
      total: 0,
      historyList: [],
      loading: false,
      refreshing: false
    })

    async function getHistoryList(page = 1, pageSize = 10) {
      if (state.loading) return;
      state.loading = true;
      state.currentPage = page;
      state.pageSize = pageSize;
      const data = {
        page,
        pageSize
      };
      const resp = await ApiGetHistoryList(data);
      state.loading = false;
      if (resp.code === 0) {
        const { list, pagination } = resp.result;
        const { total } = pagination;
        if (page === 1) {
          state.historyList = list;
        } else {
          state.historyList = [...state.historyList, ...list];
        }
        state.total = total;
      } else {
        Toast.fail(resp.msg || '获取失败');
      }
    }

    async function onRefresh() {
      state.refreshing = true;
      await getHistoryList(1);
      state.refreshing = false;
    }

    async function onLoad() {
      if (state.historyList.length >= state.total) {
        return;
      }
      await getHistoryList(state.currentPage + 1);
    }

    onMounted(() => {
      getHistoryList();
    });

    return () => (
      <EContainer>
        <EHeader title="浏览历史" />
        <EAside />
        <EContent>
          <div class={styles.history}>
            <PullRefresh v-model={state.refreshing} onRefresh={onRefresh}>
              <List
                v-model={state.loading}
                finished={state.historyList.length >= state.total}
                finished-text="没有更多了"
                onLoad={onLoad}
              >
                {state.historyList.map((item) => (
                  <div class={styles.historyItem} key={item.id}>
                    <RouterLink to={`/todo-detail-view/${item.todoId}`}>
                      <div class={styles.historyContent}>
                        <div class={styles.title}>{item.todo.title}</div>
                        <div class={styles.meta}>
                          <span class={styles.priority}>
                            优先级: {item.todo.priority}
                          </span>
                          <span class={styles.date}>
                            截止日期: {moment(item.todo.date).format('YYYY-MM-DD')}
                          </span>
                        </div>
                        <div class={styles.browseTime}>
                          浏览时间: {item.browseTime}
                        </div>
                      </div>
                    </RouterLink>
                  </div>
                ))}
              </List>
            </PullRefresh>
          </div>
        </EContent>
        <EFooter />
      </EContainer>
    );
  }
});