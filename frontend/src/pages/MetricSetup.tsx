import { ArrowRight, Loader2 } from 'lucide-react'

import { useCallback, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'

import {
  useCreateMetric,
  useExecuteSql,
  useQueryTest,
  useRecommendTables,
} from '@/features/metrics/hooks'

interface FormData {
  natural_query: string
}

const EXAMPLE_QUERIES = [
  '오늘 신규 회원가입 수',
  '최근 1시간 주문 건수',
  '평균 응답 시간',
  '에러 발생 건수',
]

export function MetricSetup() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  // SQL 미리보기 텍스트 유지 (현재 화면에 직접 표시는 queryTest.data를 사용)
  const [selectedTables, setSelectedTables] = useState<string[]>([])
  const selectedDbConnectionId = 'test-connection'
  const [generatedSql, setGeneratedSql] = useState<string>('')
  const [naturalQuery, setNaturalQuery] = useState<string>('')
  const [queryResult, setQueryResult] = useState<{
    result_type: 'single_value' | 'multiple_rows' | 'no_data'
    result_value: number | string | null
    result_data: Record<string, unknown>[] | null
    execution_time_ms?: number
  } | null>(null)

  // 추천 테이블 상태
  const [recommendedTables, setRecommendedTables] = useState<
    Array<{
      name: string
      description: string
      score: number
      columns_text: string
      common_queries: string[]
      recommendation_reason: string
    }>
  >([])

  // 알림 설정 상태
  const [notificationChannels, setNotificationChannels] = useState({
    email: false,
    slack: false,
    webhook: false,
  })
  const [notificationRecipients, setNotificationRecipients] = useState({
    'kim-data': true,
    'lee-dev': true,
    'park-manager': true,
  })

  const { register, handleSubmit, setValue } = useForm<FormData>()
  const queryTest = useQueryTest()
  const executeSql = useExecuteSql()
  const createMetric = useCreateMetric()
  const recommendTables = useRecommendTables()

  // Step 2로 이동할 때는 자동 실행하지 않음 (사용자가 버튼을 눌러야 함)

  // 지표 생성 함수
  const handleMetricCreation = useCallback(async () => {
    if (!naturalQuery) return

    console.log('지표 생성 시작:', {
      natural_query: naturalQuery,
      db_connection_id: selectedDbConnectionId,
      related_tables: selectedTables,
    })

    try {
      const result = await createMetric.mutateAsync({
        natural_query: naturalQuery,
        db_connection_id: selectedDbConnectionId,
        related_tables: selectedTables,
      })
      console.log('지표 생성 성공:', result)
    } catch (error) {
      console.error('지표 생성 실패:', error)
      alert('지표 생성에 실패했습니다: ' + (error as Error).message)
    }
  }, [naturalQuery, selectedDbConnectionId, selectedTables, createMetric])

  // 추천 테이블 목록 가져오기
  const fetchRecommendedTables = async (query: string) => {
    try {
      const result = await recommendTables.mutateAsync(query)
      setRecommendedTables(result.recommended_tables)

      // 점수가 높은 테이블들을 자동으로 선택
      const highScoreTables = result.recommended_tables
        .filter((table) => table.score >= 1.5)
        .map((table) => table.name)
      setSelectedTables(highScoreTables)
    } catch (error) {
      console.error('추천 테이블 가져오기 실패:', error)
      setRecommendedTables([])
    }
  }

  const onSubmit = async (data: FormData) => {
    if (step === 1) {
      // 자연어 쿼리 저장
      setNaturalQuery(data.natural_query)

      // SQL 생성만 하고 단계는 변경하지 않음
      const result = await queryTest.mutateAsync(data.natural_query)
      setGeneratedSql(result.sql)
      setQueryResult(result)

      // 추천 테이블 가져오기
      await fetchRecommendedTables(data.natural_query)
    }
  }

  const handleQueryExecution = async (sql: string) => {
    // SQL을 직접 실행하는 함수
    const result = await executeSql.mutateAsync(sql)
    setQueryResult(result)
  }

  return (
    <div className="flex-1 overflow-auto bg-gray-50">
      {/* 헤더 */}
      <div className="mx-auto max-w-4xl px-4 py-8 pb-1">
        <StepIndicator currentStep={step} />
      </div>

      {/* 콘텐츠 */}
      <div className="mx-auto max-w-4xl px-4 py-8">
        {step === 1 && (
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="mb-6 text-2xl font-bold text-gray-900">모니터링 지표 설정</h2>

              {/* 입력 섹션 */}
              <div className="mb-6">
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  모니터링하고 싶은 지표를 자연어로 입력하세요
                </label>
                <div className="flex space-x-3">
                  <div className="w-full">
                    <div className="relative">
                      <input
                        {...register('natural_query', { required: true })}
                        type="text"
                        placeholder="예: 오늘 신규 회원가입 수"
                        className="block w-full flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm placeholder-gray-400 focus:border-transparent focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={queryTest.isPending}
                    className="inline-flex cursor-pointer items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium whitespace-nowrap text-white transition-colors hover:bg-blue-700 disabled:bg-blue-300"
                  >
                    {queryTest.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        생성 중...
                      </>
                    ) : (
                      'SQL 생성'
                    )}
                  </button>
                </div>
              </div>

              {/* 예시 쿼리 */}
              <div className="mb-6">
                <p className="mb-3 text-sm text-gray-600">예시 쿼리:</p>
                <div className="flex flex-wrap gap-2">
                  {EXAMPLE_QUERIES.map((query) => (
                    <button
                      key={query}
                      type="button"
                      onClick={() => setValue('natural_query', query)}
                      className="cursor-pointer rounded-full bg-blue-50 px-3 py-1 text-sm text-blue-700 transition-colors hover:bg-blue-100"
                    >
                      {query}
                    </button>
                  ))}
                </div>
              </div>

              {/* SQL 생성 결과 */}
              {generatedSql && (
                <>
                  <div className="mb-6">
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      생성된 SQL 쿼리
                    </label>
                    <div className="mb-3 rounded-lg bg-gray-900 p-4">
                      <code className="font-mono text-sm text-green-400">{generatedSql}</code>
                    </div>
                    <div className="flex space-x-3">
                      <button
                        type="button"
                        onClick={() => {
                          // 현재 쿼리를 다시 실행
                          if (generatedSql) {
                            handleQueryExecution(generatedSql)
                          }
                        }}
                        disabled={executeSql.isPending}
                        className="inline-flex cursor-pointer items-center justify-center rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium whitespace-nowrap text-gray-700 transition-colors hover:bg-gray-50 disabled:bg-gray-100"
                      >
                        {executeSql.isPending ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            실행 중...
                          </>
                        ) : (
                          '쿼리 실행'
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          // SQL 편집 모드 (간단한 프롬프트로 구현)
                          const newSql = prompt('SQL을 편집하세요:', generatedSql || '')
                          if (newSql && newSql !== generatedSql) {
                            // 편집된 SQL로 다시 실행
                            setGeneratedSql(newSql)
                            handleQueryExecution(newSql)
                          }
                        }}
                        disabled={executeSql.isPending}
                        className="inline-flex cursor-pointer items-center justify-center rounded-lg px-4 py-2 text-sm font-medium whitespace-nowrap text-gray-700 transition-colors hover:bg-gray-100 disabled:text-gray-400"
                      >
                        SQL 편집
                      </button>
                    </div>
                  </div>

                  {/* 쿼리 결과 미리보기 */}
                  {queryResult && (
                    <div className="mb-6">
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        쿼리 결과 미리보기
                      </label>
                      <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                        <div className="mb-3 flex items-center space-x-2">
                          <svg
                            className="h-5 w-5 text-green-600"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <span className="font-medium text-green-800">실행 성공</span>
                          {queryResult.execution_time_ms && (
                            <span className="text-sm text-green-600">
                              ({queryResult.execution_time_ms}ms)
                            </span>
                          )}
                        </div>

                        {/* 결과 표시 */}
                        {queryResult.result_type === 'single_value' && (
                          <div className="text-lg font-semibold text-gray-900">
                            {queryResult.result_value}
                          </div>
                        )}

                        {queryResult.result_type === 'multiple_rows' && queryResult.result_data && (
                          <div>
                            <div className="mb-2 text-sm text-gray-600">
                              {queryResult.result_data.length}개 행 반환
                            </div>
                            <div className="max-h-32 overflow-y-auto">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="border-b">
                                    {Object.keys(queryResult.result_data[0] || {}).map((key) => (
                                      <th key={key} className="p-1 text-left font-medium">
                                        {key}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {queryResult.result_data.slice(0, 5).map((row, index) => (
                                    <tr key={index} className="border-b">
                                      {Object.values(row).map((value, i) => (
                                        <td key={i} className="p-1">
                                          {String(value)}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                              {queryResult.result_data.length > 5 && (
                                <div className="mt-1 text-xs text-gray-500">
                                  ... 총 {queryResult.result_data.length}개 행
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {queryResult.result_type === 'no_data' && (
                          <div className="text-gray-600">결과 없음</div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* 관련 테이블 선택 */}
                  {generatedSql && (
                    <div className="mb-6">
                      <label className="mb-3 block text-sm font-medium text-gray-700">
                        함께 모니터링할 테이블 선택
                      </label>
                      <div className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-3">
                        <div className="flex items-start space-x-2">
                          <svg
                            className="mt-0.5 h-4 w-4 text-blue-600"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <p className="text-sm text-blue-700">
                            관련 테이블들을 함께 모니터링하면 이상치 감지 정확도가 향상됩니다.
                          </p>
                        </div>
                      </div>

                      <div className="space-y-2">
                        {recommendTables.isPending ? (
                          <div className="flex items-center justify-center p-8 text-gray-500">
                            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                            추천 테이블을 분석 중...
                          </div>
                        ) : recommendedTables.length === 0 ? (
                          <div className="p-8 text-center text-gray-500">
                            추천할 테이블이 없습니다.
                          </div>
                        ) : (
                          recommendedTables.map((table) => {
                            const checked = selectedTables.includes(table.name)
                            const isHighScore = table.score >= 1.5
                            return (
                              <label
                                key={table.name}
                                className={`flex cursor-pointer items-center justify-between rounded-lg border p-3 hover:bg-gray-50 ${
                                  isHighScore ? 'border-blue-200 bg-blue-50' : 'border-gray-200'
                                }`}
                              >
                                <div className="flex items-center gap-3">
                                  <input
                                    type="checkbox"
                                    checked={checked}
                                    onChange={(e) => {
                                      setSelectedTables((prev) =>
                                        e.target.checked
                                          ? [...prev, table.name]
                                          : prev.filter((x) => x !== table.name)
                                      )
                                    }}
                                    className="h-4 w-4"
                                  />
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                      <div className="text-sm font-medium text-gray-900">
                                        {table.name}
                                      </div>
                                      {isHighScore && (
                                        <span className="rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-800">
                                          추천
                                        </span>
                                      )}
                                      <span className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
                                        점수: {table.score.toFixed(2)}
                                      </span>
                                    </div>
                                    <div className="mt-1 text-xs text-gray-600">
                                      {table.description}
                                    </div>
                                    <div className="mt-1 text-xs text-gray-500">
                                      {table.recommendation_reason}
                                    </div>
                                    {table.common_queries.length > 0 && (
                                      <div className="mt-1 text-xs text-gray-500">
                                        자주 사용: {table.common_queries.slice(0, 2).join(', ')}
                                      </div>
                                    )}
                                  </div>
                                </div>
                                <span className="rounded-full bg-green-100 px-2 py-1 text-xs text-green-800">
                                  정상
                                </span>
                              </label>
                            )
                          })
                        )}
                      </div>

                      <div className="mt-3 text-sm text-gray-600">
                        선택된 테이블: {selectedTables.length}개
                      </div>
                    </div>
                  )}

                  {/* 다음 단계 버튼 */}
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={() => setStep(2)}
                      className="inline-flex cursor-pointer items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium whitespace-nowrap text-white transition-colors hover:bg-blue-700 disabled:bg-blue-300"
                    >
                      다음 단계
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </button>
                  </div>
                </>
              )}
            </div>
          </form>
        )}

        {step === 2 && (
          <div className="rounded-xl border border-gray-200 bg-white p-8">
            <h2 className="mb-2 text-2xl font-bold text-gray-900">알림 설정</h2>
            <p className="mb-8 text-gray-600">
              이상 징후 감지 시 알림을 받을 방법과 대상을 설정하세요.
            </p>

            {/* 알림 채널 */}
            <div className="mb-8">
              <h3 className="mb-4 text-lg font-medium text-gray-900">알림 채널</h3>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                {/* 이메일 */}
                <div className="rounded-lg border border-gray-200 p-4 transition-shadow hover:shadow-sm">
                  <div className="mb-3 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100">
                        <svg
                          className="h-5 w-5 text-blue-600"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                          <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                        </svg>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">이메일</h4>
                        <p className="text-sm text-gray-600">이메일로 알림 전송</p>
                      </div>
                    </div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={notificationChannels.email}
                        onChange={(e) =>
                          setNotificationChannels((prev) => ({ ...prev, email: e.target.checked }))
                        }
                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-600">활성화</span>
                    </label>
                  </div>
                  <button
                    disabled={!notificationChannels.email}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    설정
                  </button>
                </div>

                {/* Slack */}
                <div className="rounded-lg border border-gray-200 p-4 transition-shadow hover:shadow-sm">
                  <div className="mb-3 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-100">
                        <svg
                          className="h-5 w-5 text-purple-600"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">Slack</h4>
                        <p className="text-sm text-gray-600">Slack 채널로 알림</p>
                      </div>
                    </div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={notificationChannels.slack}
                        onChange={(e) =>
                          setNotificationChannels((prev) => ({ ...prev, slack: e.target.checked }))
                        }
                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-600">활성화</span>
                    </label>
                  </div>
                  <button
                    disabled={!notificationChannels.slack}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    설정
                  </button>
                </div>

                {/* Webhook */}
                <div className="rounded-lg border border-gray-200 p-4 transition-shadow hover:shadow-sm">
                  <div className="mb-3 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-100">
                        <svg
                          className="h-5 w-5 text-green-600"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">Webhook</h4>
                        <p className="text-sm text-gray-600">API 엔드포인트로 전송</p>
                      </div>
                    </div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={notificationChannels.webhook}
                        onChange={(e) =>
                          setNotificationChannels((prev) => ({
                            ...prev,
                            webhook: e.target.checked,
                          }))
                        }
                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-600">활성화</span>
                    </label>
                  </div>
                  <button
                    disabled={!notificationChannels.webhook}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    설정
                  </button>
                </div>
              </div>
            </div>

            {/* 알림 대상 */}
            <div className="mb-8">
              <h3 className="mb-4 text-lg font-medium text-gray-900">알림 대상</h3>
              <div className="space-y-3">
                {/* 김데이터 */}
                <div className="flex items-center justify-between rounded-lg border border-gray-200 p-4">
                  <div className="flex items-center space-x-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600">
                      <span className="text-sm font-medium text-white">김</span>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">김데이터</h4>
                      <p className="text-sm text-gray-600">데이터 분석가 • data@company.com</p>
                    </div>
                  </div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={notificationRecipients['kim-data']}
                      onChange={(e) =>
                        setNotificationRecipients((prev) => ({
                          ...prev,
                          'kim-data': e.target.checked,
                        }))
                      }
                      className="h-4 w-4 rounded border-gray-300 text-pink-600 focus:ring-pink-500"
                    />
                    <span className="ml-2 text-sm text-gray-600">알림 받기</span>
                  </label>
                </div>

                {/* 이개발 */}
                <div className="flex items-center justify-between rounded-lg border border-gray-200 p-4">
                  <div className="flex items-center space-x-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600">
                      <span className="text-sm font-medium text-white">이</span>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">이개발</h4>
                      <p className="text-sm text-gray-600">백엔드 개발자 • dev@company.com</p>
                    </div>
                  </div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={notificationRecipients['lee-dev']}
                      onChange={(e) =>
                        setNotificationRecipients((prev) => ({
                          ...prev,
                          'lee-dev': e.target.checked,
                        }))
                      }
                      className="h-4 w-4 rounded border-gray-300 text-pink-600 focus:ring-pink-500"
                    />
                    <span className="ml-2 text-sm text-gray-600">알림 받기</span>
                  </label>
                </div>

                {/* 박매니저 */}
                <div className="flex items-center justify-between rounded-lg border border-gray-200 p-4">
                  <div className="flex items-center space-x-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600">
                      <span className="text-sm font-medium text-white">박</span>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">박매니저</h4>
                      <p className="text-sm text-gray-600">프로덕트 매니저 • pm@company.com</p>
                    </div>
                  </div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={notificationRecipients['park-manager']}
                      onChange={(e) =>
                        setNotificationRecipients((prev) => ({
                          ...prev,
                          'park-manager': e.target.checked,
                        }))
                      }
                      className="h-4 w-4 rounded border-gray-300 text-pink-600 focus:ring-pink-500"
                    />
                    <span className="ml-2 text-sm text-gray-600">알림 받기</span>
                  </label>
                </div>
              </div>
            </div>

            {/* 네비게이션 버튼 */}
            <div className="flex items-center justify-between">
              <button
                onClick={() => setStep(1)}
                className="rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50"
              >
                이전 단계
              </button>
              <button
                onClick={async () => {
                  console.log('설정 완료 버튼 클릭 - 지표 생성 시작')
                  try {
                    await handleMetricCreation()
                    setStep(3) // 성공 시에만 진행
                  } catch (error) {
                    console.error('지표 생성 실패:', error)
                    alert('지표 생성에 실패했습니다. 설정을 확인하고 다시 시도해 주세요.')
                  }
                }}
                disabled={createMetric.isPending}
                className="rounded-lg bg-blue-600 px-6 py-3 text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
              >
                {createMetric.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    지표 생성 중...
                  </>
                ) : (
                  '설정 완료'
                )}
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="text-center">
            {/* 성공 아이콘 */}
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
              <svg
                className="h-8 w-8 text-green-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>

            {/* 완료 메시지 */}
            <h2 className="mb-8 text-3xl font-bold text-gray-900">설정이 완료되었습니다!</h2>

            {/* 설정 요약 카드 */}
            <div className="mx-auto mb-8 max-w-2xl rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
              <h3 className="mb-6 text-left text-lg font-medium text-gray-900">설정 요약</h3>

              <div className="space-y-4 text-left">
                {/* 지표 정보 */}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">지표</span>
                  <span className="text-sm font-medium text-gray-900">
                    {generatedSql ? 'SQL 기반 지표' : '자연어 쿼리'}
                  </span>
                </div>

                {/* SQL 쿼리 */}
                {generatedSql && (
                  <div className="flex items-start justify-between">
                    <span className="text-sm text-gray-600">SQL</span>
                    <code className="max-w-md rounded border border-gray-200 bg-gray-50 px-3 py-2 text-right font-mono text-sm text-gray-900">
                      {generatedSql}
                    </code>
                  </div>
                )}

                {/* 모니터링 테이블 */}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">모니터링 테이블</span>
                  <span className="text-sm font-medium text-gray-900">
                    {selectedTables.length}개
                  </span>
                </div>

                {/* 모니터링 주기 */}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">모니터링 주기</span>
                  <span className="text-sm font-medium text-gray-900">1시간</span>
                </div>

                {/* 이상치 감지 */}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">이상치 감지</span>
                  <span className="text-sm font-medium text-gray-900">활성화</span>
                </div>

                {/* 알림 채널 */}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">알림 채널</span>
                  <span className="text-sm font-medium text-gray-900">
                    {Object.values(notificationChannels).filter(Boolean).length}개 활성화
                  </span>
                </div>

                {/* 알림 대상 */}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">알림 대상</span>
                  <span className="text-sm font-medium text-gray-900">
                    {Object.values(notificationRecipients).filter(Boolean).length}명
                  </span>
                </div>
              </div>
            </div>

            {/* 네비게이션 버튼 */}
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => setStep(2)}
                className="rounded-lg border border-gray-300 px-6 py-3 text-gray-700 hover:bg-gray-50"
              >
                이전 단계
              </button>
              <button
                onClick={() => navigate('/dashboard')}
                className="rounded-lg bg-blue-600 px-6 py-3 text-white hover:bg-blue-700"
              >
                대시보드로 이동
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function StepIndicator({ currentStep }: { currentStep: number }) {
  const steps = [
    { number: 1, label: '지표 설정' },
    { number: 2, label: '알림 설정' },
    { number: 3, label: '설정 완료' },
  ]

  return (
    <div className="flex items-center justify-center space-x-8">
      {steps.map((step, idx) => (
        <div key={step.number} className="flex items-center">
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-medium ${
              step.number === currentStep
                ? 'bg-blue-600 text-white'
                : step.number < currentStep
                  ? 'bg-gray-200 text-gray-600'
                  : 'bg-gray-200 text-gray-600'
            } `}
          >
            {step.number}
          </div>
          <div className="ml-3 text-sm">{step.label}</div>
          {idx < steps.length - 1 && <div className="ml-8 h-0.5 w-16 bg-gray-200" />}
        </div>
      ))}
    </div>
  )
}
