pipeline {
    agent any

    environment {
        DATABASE_URL = "postgresql://devops:devpass123@localhost:5433/devopslab"
        IMAGE_NAME = "devops-lab-app"
        VM1_IP = "192.168.56.103"
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

        stage('Build Docker image') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} ."
                sh "docker tag ${IMAGE_NAME}:${BUILD_NUMBER} ${IMAGE_NAME}:latest"
            }
        }

        stage('Deploy to vm1') {
            steps {
                sshagent(credentials: ['vm1-ssh-key']) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no devops@${VM1_IP} "
                            cd ~/devops-lab &&
                            git pull &&
                            docker compose up -d --build
                        "
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'docker rm -f test-postgres || true'
        }
        success {
            echo "Build #${BUILD_NUMBER} deployed successfully to vm1"
        }
        failure {
            echo 'Pipeline failed.'
        }
    }
}
