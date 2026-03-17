pipeline {
    agent any

    environment {
        DOCKER_IMAGE_NAME    = 'task-automation-cli'
        GITHUB_REPO_URL      = 'https://github.com/Mohit1-cmd/Python_TaskScheduler.git'
        DOCKER_HUB_USERNAME  = 'mohit67'
    }

    stages {

        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }

        stage('Checkout Source Code') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: "${GITHUB_REPO_URL}",
                        credentialsId: 'github_credentials'
                    ]]
                ])
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                python3 -m venv .venv
                .venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '.venv/bin/python -m pytest tests/ -v --tb=short'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE_NAME}")
                }
            }
        }

        stage('Push Docker Image to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-hub-credential',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                    echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                    docker tag ${DOCKER_IMAGE_NAME}:latest ${DOCKER_HUB_USERNAME}/${DOCKER_IMAGE_NAME}:latest
                    docker push ${DOCKER_HUB_USERNAME}/${DOCKER_IMAGE_NAME}:latest
                    """
                }
            }
        }

        stage('Deploy with Ansible') {
            steps {
                ansiblePlaybook(
                    playbook: 'ansible/deploy.yml',
                    inventory: 'ansible/inventory'
                )
            }
        }

    }

    post {

        success {
            mail to: 'aezakmi7974@gmail.com',
                 subject: "✅ Jenkins SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                 body: """
Build completed successfully.

Job          : ${env.JOB_NAME}
Build Number : ${env.BUILD_NUMBER}
Details      : ${env.BUILD_URL}
"""
        }

        failure {
            mail to: 'aezakmi7974@gmail.com',
                 subject: "❌ Jenkins FAILURE: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                 body: """
Build failed.

Job          : ${env.JOB_NAME}
Build Number : ${env.BUILD_NUMBER}
Logs         : ${env.BUILD_URL}
"""
        }

    }
}
