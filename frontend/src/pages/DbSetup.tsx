import { CheckCircle, Clock, Database, Loader2, XCircle } from 'lucide-react'

import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'

import {
  useCreateDbConnection,
  useSetupStatus,
  useStartSetup,
  useTestConnection,
} from '@/features/metrics/hooks'

interface FormData {
  name: string
  host: string
  port: number
  database: string
  username: string
  password: string
}

export function DbSetup() {
  const [step, setStep] = useState<'form' | 'setup' | 'complete'>('form')
  const [connectionId, setConnectionId] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [setupStarted, setSetupStarted] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>()
  const createConnection = useCreateDbConnection()
  const testConnection = useTestConnection()
  const startSetup = useStartSetup()
  const { data: setupStatus } = useSetupStatus(connectionId || undefined, setupStarted)

  const onSubmit = async (data: FormData) => {
    if (step === 'form') {
      // DB 연결 생성
      try {
        const connection = await createConnection.mutateAsync(data)
        setConnectionId(connection.id)

        // 즉시 연결 테스트
        const test = await testConnection.mutateAsync(connection.id)
        setTestResult({ success: test.success, message: test.message })

        if (test.success) {
          setStep('setup')
        }
      } catch (error) {
        console.error('연결 생성 실패:', error)
      }
    }
  }

  const handleStartSetup = async () => {
    if (connectionId) {
      try {
        await startSetup.mutateAsync(connectionId)
        setSetupStarted(true) // 폴링 시작
        setStep('setup')
      } catch (error) {
        console.error('설정 시작 실패:', error)
      }
    }
  }

  // 설정 완료 감지
  useEffect(() => {
    if (setupStatus?.status === 'success') {
      setStep('complete')
    }
  }, [setupStatus?.status])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-4xl px-4 py-8">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className="mb-2 text-3xl font-bold text-gray-900">DB 연결 설정</h1>
          <p className="text-gray-600">
            PostgreSQL 데이터베이스에 연결하고 AI 모니터링을 설정하세요
          </p>
        </div>

        {/* 단계 표시기 */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-8">
            <div
              className={`flex items-center ${step === 'form' ? 'text-blue-600' : 'text-gray-400'}`}
            >
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full ${
                  step === 'form' ? 'bg-blue-600 text-white' : 'bg-gray-200'
                }`}
              >
                1
              </div>
              <span className="ml-2 font-medium">연결 정보</span>
            </div>
            <div
              className={`h-0.5 w-16 ${step === 'setup' || step === 'complete' ? 'bg-blue-600' : 'bg-gray-200'}`}
            />
            <div
              className={`flex items-center ${step === 'setup' ? 'text-blue-600' : step === 'complete' ? 'text-green-600' : 'text-gray-400'}`}
            >
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full ${
                  step === 'setup'
                    ? 'bg-blue-600 text-white'
                    : step === 'complete'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-200'
                }`}
              >
                2
              </div>
              <span className="ml-2 font-medium">자동 설정</span>
            </div>
            <div className={`h-0.5 w-16 ${step === 'complete' ? 'bg-green-600' : 'bg-gray-200'}`} />
            <div
              className={`flex items-center ${step === 'complete' ? 'text-green-600' : 'text-gray-400'}`}
            >
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full ${
                  step === 'complete' ? 'bg-green-600 text-white' : 'bg-gray-200'
                }`}
              >
                3
              </div>
              <span className="ml-2 font-medium">완료</span>
            </div>
          </div>
        </div>

        {/* 폼 단계 */}
        {step === 'form' && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
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
                  <label className="mb-2 block text-sm font-medium text-gray-700">호스트 *</label>
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
                  <label className="mb-2 block text-sm font-medium text-gray-700">사용자명 *</label>
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
                  <label className="mb-2 block text-sm font-medium text-gray-700">비밀번호 *</label>
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
                  onClick={() => window.history.back()}
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

        {/* 설정 단계 */}
        {step === 'setup' && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
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

                {/* 단계별 상태 */}
                <div className="space-y-3">
                  {setupStatus.steps.map((step, index) => (
                    <div
                      key={index}
                      className="flex items-center space-x-3 rounded-lg bg-gray-50 p-3"
                    >
                      <div className="flex-shrink-0">
                        {step.status === 'pending' && <Clock className="h-5 w-5 text-gray-400" />}
                        {step.status === 'running' && (
                          <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                        )}
                        {step.status === 'success' && (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        )}
                        {step.status === 'error' && <XCircle className="h-5 w-5 text-red-600" />}
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

            <div className="mt-8 text-center">
              <button
                onClick={handleStartSetup}
                disabled={startSetup.isPending}
                className="mx-auto flex items-center rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 disabled:bg-blue-300"
              >
                {startSetup.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                설정 시작
              </button>
            </div>
          </div>
        )}

        {/* 완료 단계 */}
        {step === 'complete' && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-center shadow-sm">
            <CheckCircle className="mx-auto mb-4 h-16 w-16 text-green-600" />
            <h2 className="mb-2 text-2xl font-semibold text-gray-900">설정 완료!</h2>
            <p className="mb-8 text-gray-600">
              데이터베이스 연결과 AI 모니터링 설정이 완료되었습니다.
            </p>
            <div className="space-y-4">
              <button
                onClick={() => (window.location.href = '/dashboard')}
                className="rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700"
              >
                대시보드로 이동
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
    </div>
  )
}
