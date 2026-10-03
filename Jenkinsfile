pipeline {
    agent any

    environment {
        DATABASE_URL = "postgresql://devops:devpass123@localhost:5433/devopslab"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Start test database') {
            steps {
                sh '''
                    docker rm -f test-postgres || true
                    docker run -d --name test-postgres \
                        -e POSTGRES_USER=devops \
                        -e POSTGRES_PASSWORD=devpass123 \
                        -e POSTGRES_DB=devopslab \
                        -p 5433:5432 \
                        postgres:16
                    echo "Waiting for Postgres to be ready..."
                    sleep 8
                '''
            }
        }

        stage('Install dependencies') {
            steps {
                sh 'python3 -m venv venv'
                sh '. venv/bin/activate && pip install -r requirements.txt'
            }
        }

        stage('Run tests') {
            steps {
                sh '. venv/bin/activate && pytest'
            }
        }
    }

    post {
        always {
            sh 'docker rm -f test-postgres || true'
        }
        success {
            echo 'Build and tests passed!'
        }
        failure {
            echo 'Build or tests failed.'
        }
    }
}
