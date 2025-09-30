import {
  CheckCircle,
  Clock,
  Database,
  Edit,
  Loader2,
  Play,
  Plus,
  TestTube,
  Trash2,
  XCircle,
} from 'lucide-react'

import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'

import {
  useCreateDbConnection,
  useDbConnections,
  useDeleteDbConnection,
  useSetupStatus,
  useStartSetup,
  useTestConnection,
  useUpdateDbConnection,
} from '@/features/metrics/hooks'

interface FormData {
  name: string
  host: string
  port: number
  database: string
  username: string
  password: string
}

export function DbConnections() {
  const [showForm, setShowForm] = useState(false)
  const [editingConnection, setEditingConnection] = useState<string | null>(null)
  const [setupStep, setSetupStep] = useState<'form' | 'setup' | 'complete' | null>(null)
  const [connectionId, setConnectionId] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [setupStarted, setSetupStarted] = useState(false)

  const { data: connectionsData, isLoading } = useDbConnections()
  const createConnection = useCreateDbConnection()
  const updateConnection = useUpdateDbConnection()
  const deleteConnection = useDeleteDbConnection()
  const testConnection = useTestConnection()
  const startSetup = useStartSetup()
  const { data: setupStatus } = useSetupStatus(connectionId || undefined, setupStarted)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FormData>()

  const connections = connectionsData?.items || []

  const onSubmit = async (data: FormData) => {
    try {
      if (editingConnection) {
        await updateConnection.mutateAsync({ id: editingConnection, data })
        setEditingConnection(null)
        setShowForm(false)
        reset()
      } else {
        // 새 연결 생성 시 3단계 프로세스 시작
        const connection = await createConnection.mutateAsync(data)
        setConnectionId(connection.id)

        // 즉시 연결 테스트
        const test = await testConnection.mutateAsync(connection.id)
        setTestResult({ success: test.success, message: test.message })

        if (test.success) {
          setSetupStep('setup')
        } else {
          setSetupStep('form') // 테스트 실패 시 폼으로 돌아감
        }
      }
    } catch (error) {
      console.error('연결 저장 실패:', error)
    }
  }

  const handleEdit = (connection: {
    id: string
    name: string
    host: string
    port: number
    database: string
    username: string
  }) => {
    setEditingConnection(connection.id)
    reset({
      name: connection.name,
      host: connection.host,
      port: connection.port,
      database: connection.database,
      username: connection.username,
      password: '',
    })
    setShowForm(true)
  }

  const handleDelete = async (connectionId: string) => {
    if (confirm('정말로 이 연결을 삭제하시겠습니까?')) {
      try {
        await deleteConnection.mutateAsync(connectionId)
      } catch (error) {
        console.error('연결 삭제 실패:', error)
      }
    }
  }

  const handleTest = async (connectionId: string) => {
    try {
      await testConnection.mutateAsync(connectionId)
    } catch (error) {
      console.error('연결 테스트 실패:', error)
    }
  }

  const handleStartSetup = async (connectionId: string) => {
    try {
      await startSetup.mutateAsync(connectionId)
      setConnectionId(connectionId)
      setSetupStarted(true) // 폴링 시작
      setSetupStep('setup') // 2단계로 이동
    } catch (error) {
      console.error('설정 시작 실패:', error)
    }
  }

  const handleStartSetupFromForm = async () => {
    if (connectionId) {
      try {
        await startSetup.mutateAsync(connectionId)
        setSetupStarted(true) // 폴링 시작
        setSetupStep('setup')
      } catch (error) {
        console.error('설정 시작 실패:', error)
      }
    }
  }

  // 설정 완료 감지
  useEffect(() => {
    if (setupStatus?.status === 'success') {
      setSetupStep('complete')
    }
  }, [setupStatus?.status])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />
      case 'inactive':
        return <Clock className="h-4 w-4 text-gray-400" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return '활성'
      case 'error':
        return '오류'
      case 'inactive':
        return '비활성'
      default:
        return '알 수 없음'
    }
  }

  return (
    <div className="min-h-screen w-full flex-1 bg-gray-50">
      <div className="mx-auto max-w-4xl px-4 py-8">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className="mb-2 text-3xl font-bold text-gray-900">DB 연결 관리</h1>
          <p className="text-gray-600">데이터베이스 연결을 관리하고 모니터링을 설정하세요</p>
        </div>

        {/* 연결 목록 */}
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">연결된 데이터베이스</h2>
              <button
                onClick={() => {
                  setSetupStep('form')
                  setShowForm(false)
                  setEditingConnection(null)
                  setConnectionId(null)
                  setTestResult(null)
                  setSetupStarted(false)
                  reset()
                }}
                className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
              >
                <Plus className="mr-2 h-4 w-4" />새 연결 추가
              </button>
            </div>
          </div>

          {isLoading ? (
            <div className="p-8 text-center">
              <Loader2 className="mx-auto mb-4 h-8 w-8 animate-spin text-gray-400" />
              <p className="text-gray-500">연결 목록을 불러오는 중...</p>
            </div>
          ) : connections.length === 0 ? (
            <div className="p-8 text-center">
              <Database className="mx-auto mb-4 h-12 w-12 text-gray-400" />
              <p className="mb-4 text-gray-500">아직 연결된 데이터베이스가 없습니다</p>
              <button
                onClick={() => {
                  setSetupStep('form')
                  setShowForm(false)
                  setEditingConnection(null)
                  setConnectionId(null)
                  setTestResult(null)
                  setSetupStarted(false)
                  reset()
                }}
                className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
              >
                <Plus className="mr-2 h-4 w-4" />첫 연결 추가하기
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {connections.map((connection) => (
                <div key={connection.id} className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <Database className="h-8 w-8 text-blue-600" />
                      <div>
                        <h3 className="text-lg font-medium text-gray-900">{connection.name}</h3>
                        <p className="text-sm text-gray-500">
                          {connection.host}:{connection.port}/{connection.database}
                        </p>
                        <div className="mt-1 flex items-center space-x-2">
                          {getStatusIcon(connection.status)}
                          <span className="text-sm text-gray-600">
                            {getStatusText(connection.status)}
                          </span>
                          {connection.last_tested_at && (
                            <span className="text-xs text-gray-400">
                              마지막 테스트: {new Date(connection.last_tested_at).toLocaleString()}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleTest(connection.id)}
                        disabled={testConnection.isPending}
                        className="inline-flex items-center rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                      >
                        {testConnection.isPending ? (
                          <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                        ) : (
                          <TestTube className="mr-1 h-4 w-4" />
                        )}
                        테스트
                      </button>
                      <button
                        onClick={() => handleStartSetup(connection.id)}
                        disabled={
                          startSetup.isPending || (setupStarted && setupStatus?.status !== 'error')
                        }
                        className="inline-flex items-center rounded-lg bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700 disabled:opacity-50"
                      >
                        {(startSetup.isPending ||
                          (setupStarted && setupStatus?.status === 'running')) && (
                          <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                        )}
                        {!startSetup.isPending &&
                          !(setupStarted && setupStatus?.status === 'running') && (
                            <Play className="mr-1 h-4 w-4" />
                          )}
                        설정 시작
                      </button>
                      <button
                        onClick={() => handleEdit(connection)}
                        className="inline-flex items-center rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-200"
                      >
                        <Edit className="mr-1 h-4 w-4" />
                        수정
                      </button>
                      <button
                        onClick={() => handleDelete(connection.id)}
                        className="inline-flex items-center rounded-lg bg-red-100 px-3 py-1.5 text-sm text-red-700 hover:bg-red-200"
                      >
                        <Trash2 className="mr-1 h-4 w-4" />
                        삭제
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 3단계 프로세스 */}
        {setupStep && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            {/* 단계 표시기 */}
            <div className="mb-8">
              <div className="flex items-center justify-center space-x-8">
                <div
                  className={`flex items-center ${setupStep === 'form' ? 'text-blue-600' : 'text-gray-400'}`}
                >
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-full ${
                      setupStep === 'form' ? 'bg-blue-600 text-white' : 'bg-gray-200'
                    }`}
                  >
                    1
                  </div>
                  <span className="ml-2 font-medium">연결 정보</span>
                </div>
                <div
                  className={`h-0.5 w-16 ${setupStep === 'setup' || setupStep === 'complete' ? 'bg-blue-600' : 'bg-gray-200'}`}
                />
                <div
                  className={`flex items-center ${setupStep === 'setup' ? 'text-blue-600' : setupStep === 'complete' ? 'text-green-600' : 'text-gray-400'}`}
                >
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-full ${
                      setupStep === 'setup'
                        ? 'bg-blue-600 text-white'
                        : setupStep === 'complete'
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-200'
                    }`}
                  >
                    2
                  </div>
                  <span className="ml-2 font-medium">자동 설정</span>
                </div>
                <div
                  className={`h-0.5 w-16 ${setupStep === 'complete' ? 'bg-green-600' : 'bg-gray-200'}`}
                />
                <div
                  className={`flex items-center ${setupStep === 'complete' ? 'text-green-600' : 'text-gray-400'}`}
                >
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-full ${
                      setupStep === 'complete' ? 'bg-green-600 text-white' : 'bg-gray-200'
                    }`}
                  >
                    3
                  </div>
                  <span className="ml-2 font-medium">완료</span>
                </div>
              </div>
            </div>

            {/* 1단계: 연결 정보 입력 */}
            {setupStep === 'form' && (
              <div>
                <h2 className="mb-6 text-xl font-semibold text-gray-900">데이터베이스 연결 정보</h2>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                  <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        연결 이름 *
                      </label>
                      <input
                        {...register('name', { required: '연결 이름을 입력하세요' })}
                        type="text"
                        placeholder="예: 프로덕션 DB"
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      />
                      {errors.name && (
                        <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                      )}
                    </div>

                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        호스트 *
                      </label>
                      <input
                        {...register('host', { required: '호스트를 입력하세요' })}
                        type="text"
                        placeholder="localhost"
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      />
                      {errors.host && (
                        <p className="mt-1 text-sm text-red-600">{errors.host.message}</p>
                      )}
                    </div>

                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">포트 *</label>
                      <input
                        {...register('port', {
                          required: '포트를 입력하세요',
                          valueAsNumber: true,
                          min: { value: 1, message: '유효한 포트 번호를 입력하세요' },
                          max: { value: 65535, message: '유효한 포트 번호를 입력하세요' },
                        })}
                        type="number"
                        placeholder="5432"
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      />
                      {errors.port && (
                        <p className="mt-1 text-sm text-red-600">{errors.port.message}</p>
                      )}
                    </div>

                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        데이터베이스명 *
                      </label>
                      <input
                        {...register('database', { required: '데이터베이스명을 입력하세요' })}
                        type="text"
                        placeholder="ecommerce_db"
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      />
                      {errors.database && (
                        <p className="mt-1 text-sm text-red-600">{errors.database.message}</p>
                      )}
                    </div>

                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        사용자명 *
                      </label>
                      <input
                        {...register('username', { required: '사용자명을 입력하세요' })}
                        type="text"
                        placeholder="monitoring_user"
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      />
                      {errors.username && (
                        <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
                      )}
                    </div>

                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        비밀번호 *
                      </label>
                      <input
                        {...register('password', { required: '비밀번호를 입력하세요' })}
                        type="password"
                        placeholder="••••••••"
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      />
                      {errors.password && (
                        <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
                      )}
                    </div>
                  </div>

                  {/* 연결 테스트 결과 */}
                  {testResult && (
                    <div
                      className={`rounded-lg p-4 ${
                        testResult.success
                          ? 'border border-green-200 bg-green-50'
                          : 'border border-red-200 bg-red-50'
                      }`}
                    >
                      <div className="flex items-center">
                        {testResult.success ? (
                          <CheckCircle className="mr-2 h-5 w-5 text-green-600" />
                        ) : (
                          <XCircle className="mr-2 h-5 w-5 text-red-600" />
                        )}
                        <span className={testResult.success ? 'text-green-800' : 'text-red-800'}>
                          {testResult.message}
                        </span>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end space-x-4">
                    <button
                      type="button"
                      onClick={() => {
                        setSetupStep(null)
                        setConnectionId(null)
                        setTestResult(null)
                        setSetupStarted(false)
                        reset()
                      }}
                      className="rounded-lg bg-gray-100 px-4 py-2 text-gray-700 hover:bg-gray-200"
                    >
                      취소
                    </button>
                    <button
                      type="submit"
                      disabled={createConnection.isPending || testConnection.isPending}
                      className="flex items-center rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 disabled:bg-blue-300"
                    >
                      {(createConnection.isPending || testConnection.isPending) && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      연결 테스트
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* 2단계: 자동 설정 (5단계 프로세스) */}
            {setupStep === 'setup' && (
              <div>
                <div className="mb-8 text-center">
                  <Database className="mx-auto mb-4 h-16 w-16 text-blue-600" />
                  <h2 className="mb-2 text-2xl font-semibold text-gray-900">자동 설정 진행 중</h2>
                  <p className="text-gray-600">
                    데이터베이스 스키마를 분석하고 AI 모니터링을 설정하고 있습니다
                  </p>
                </div>

                {setupStatus && (
                  <div className="space-y-4">
                    {/* 진행률 바 */}
                    <div className="mb-6">
                      <div className="mb-2 flex justify-between text-sm text-gray-600">
                        <span>진행률</span>
                        <span>{Math.round(setupStatus.progress_percentage)}%</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-gray-200">
                        <div
                          className="h-2 rounded-full bg-blue-600 transition-all duration-300"
                          style={{ width: `${setupStatus.progress_percentage}%` }}
                        />
                      </div>
                    </div>

                    {/* 5단계 프로세스 상태 */}
                    <div className="space-y-3">
                      {setupStatus.steps.map((step, index) => (
                        <div
                          key={index}
                          className="flex items-center space-x-3 rounded-lg bg-gray-50 p-3"
                        >
                          <div className="flex-shrink-0">
                            {step.status === 'pending' && (
                              <Clock className="h-5 w-5 text-gray-400" />
                            )}
                            {step.status === 'running' && (
                              <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                            )}
                            {step.status === 'success' && (
                              <CheckCircle className="h-5 w-5 text-green-600" />
                            )}
                            {step.status === 'error' && (
                              <XCircle className="h-5 w-5 text-red-600" />
                            )}
                          </div>
                          <div className="flex-1">
                            <div className="font-medium text-gray-900">{step.name}</div>
                            <div className="text-sm text-gray-600">{step.message}</div>
                            {step.error_details && (
                              <div className="mt-1 text-sm text-red-600">{step.error_details}</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 설정이 아직 시작되지 않은 경우 */}
                {!setupStarted && (
                  <div className="mt-8 text-center">
                    <button
                      onClick={handleStartSetupFromForm}
                      disabled={
                        startSetup.isPending || (setupStarted && setupStatus?.status !== 'error')
                      }
                      className="mx-auto flex items-center rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 disabled:bg-blue-300"
                    >
                      {(startSetup.isPending ||
                        (setupStarted && setupStatus?.status === 'running')) && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      설정 시작
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* 3단계: 완료 */}
            {setupStep === 'complete' && (
              <div className="text-center">
                <CheckCircle className="mx-auto mb-4 h-16 w-16 text-green-600" />
                <h2 className="mb-2 text-2xl font-semibold text-gray-900">설정 완료!</h2>
                <p className="mb-8 text-gray-600">
                  데이터베이스 연결과 AI 모니터링 설정이 완료되었습니다.
                </p>
                <div className="space-y-4">
                  <button
                    onClick={() => {
                      setSetupStep(null)
                      setConnectionId(null)
                      setTestResult(null)
                      setSetupStarted(false)
                      reset()
                    }}
                    className="rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700"
                  >
                    연결 목록으로 돌아가기
                  </button>
                  <button
                    onClick={() => (window.location.href = '/setup')}
                    className="ml-4 rounded-lg bg-gray-100 px-6 py-2 text-gray-700 hover:bg-gray-200"
                  >
                    지표 설정하기
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 연결 수정 폼 */}
        {showForm && (
          <div className="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4">
            <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white shadow-xl">
              <div className="border-b border-gray-200 px-6 py-4">
                <h3 className="text-lg font-semibold text-gray-900">연결 수정</h3>
              </div>

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 p-6">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      연결 이름 *
                    </label>
                    <input
                      {...register('name', { required: '연결 이름을 입력하세요' })}
                      type="text"
                      placeholder="예: 프로덕션 DB"
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                    {errors.name && (
                      <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">호스트 *</label>
                    <input
                      {...register('host', { required: '호스트를 입력하세요' })}
                      type="text"
                      placeholder="localhost"
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                    {errors.host && (
                      <p className="mt-1 text-sm text-red-600">{errors.host.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">포트 *</label>
                    <input
                      {...register('port', {
                        required: '포트를 입력하세요',
                        valueAsNumber: true,
                        min: { value: 1, message: '유효한 포트 번호를 입력하세요' },
                        max: { value: 65535, message: '유효한 포트 번호를 입력하세요' },
                      })}
                      type="number"
                      placeholder="5432"
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                    {errors.port && (
                      <p className="mt-1 text-sm text-red-600">{errors.port.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      데이터베이스명 *
                    </label>
                    <input
                      {...register('database', { required: '데이터베이스명을 입력하세요' })}
                      type="text"
                      placeholder="ecommerce_db"
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                    {errors.database && (
                      <p className="mt-1 text-sm text-red-600">{errors.database.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      사용자명 *
                    </label>
                    <input
                      {...register('username', { required: '사용자명을 입력하세요' })}
                      type="text"
                      placeholder="monitoring_user"
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                    {errors.username && (
                      <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      비밀번호 *
                    </label>
                    <input
                      {...register('password', { required: '비밀번호를 입력하세요' })}
                      type="password"
                      placeholder="••••••••"
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                    {errors.password && (
                      <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
                    )}
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowForm(false)
                      setEditingConnection(null)
                      reset()
                    }}
                    className="rounded-lg bg-gray-100 px-4 py-2 text-gray-700 hover:bg-gray-200"
                  >
                    취소
                  </button>
                  <button
                    type="submit"
                    disabled={updateConnection.isPending}
                    className="flex items-center rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {updateConnection.isPending && (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    )}
                    수정
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
